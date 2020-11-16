import bpy
import inspect
import logging
from pprint import pprint
from typing import *
from gensim.models import Word2Vec


def get_reports(context) -> List[str]:
    """A hacky way to get all reports from blender

    Report is most often function call or value assignment but there can occur also unstructured messages

    :return: list of reports
    """
    win = context.window_manager.windows[0]
    area = win.screen.areas[0]
    area_type = area.type
    area.type = 'INFO'
    override = context.copy()
    override['window'] = win
    override['screen'] = win.screen
    override['area'] = win.screen.areas[0]
    bpy.ops.info.select_all(override, action='SELECT')
    bpy.ops.info.report_copy(override)
    area.type = area_type
    clipboard: str = context.window_manager.clipboard
    # bpy.data.texts.new("Recent Reports")
    # bpy.data.texts['Recent Reports'].write(clipboard)
    return clipboard.splitlines()


def get_operator_reports(context) -> List[str]:
    return [report for report in get_reports(context) if report.startswith('bpy.ops')]


def _list_blender_operators() -> List[bpy.types.Operator]:
    """Get all valid operators for given context.

    This list can change during blender runtime, addons can register new operators
    """
    result = []
    for module_name, module in inspect.getmembers(bpy.ops):
        for attribute, operator in inspect.getmembers(module):
            result.append(operator)
    return result


class VocabCorpus:
    def __iter__(self):
        for line in open('vocab.txt'):
            yield [line.replace('\n', '')]


class Prediction:
    def __init__(self, operator: bpy.types.Operator, rank: float, operator_arguments: Dict[str, Any] = None):
        self.operator = operator
        self.rank = rank
        self.operator_arguments = operator_arguments or {}


def predict(context: Dict,
            blender_operators: List[bpy.types.Operator],
            reports: List[str]) -> List[Prediction]:
    """
       :param context: copy of blender context, can be used for checking which operators can be executed: Operator.poll(context)
       :param blender_operators: list of possible operators
       :param reports: history of user actions
       :return: list of predictions
       """

    with open("vocab.txt", "w") as vocab_file:
        for op in blender_operators:
            vocab_file.write(op.idname_py())
            vocab_file.write('\n')

    with open("history.txt", "a") as f:
        for report in reports:
            f.write(report.split('(')[0][8:] + '\n')

    name_to_operator = dict((operator.idname_py(), operator) for operator in blender_operators)

    model, last_operation = train_word2vec("history.txt")
    valid_operator_names = {op.idname_py() for op in blender_operators if op.poll(context)}
    similar_operators = model.most_similar(positive=[last_operation], topn=3)
    return list(
        Prediction(operator=name_to_operator.get(similar_operator[0]), rank=similar_operator[1]) for similar_operator in
        similar_operators  # if similar_operators[0] in valid_operator_names
    )


def train_word2vec(history_file):
    words = []
    with open(history_file, 'r') as f:
        for line in f.readlines():
            words.append(line.replace('\n', ''))

    last_operation = words[len(words) - 1]

    sentences = VocabCorpus()
    model = Word2Vec()
    model.build_vocab(sentences=sentences, min_count=1)
    model.train(words, total_words=model.corpus_count, epochs=10)

    return model, last_operation


class WM_OT_predict_operator(bpy.types.Operator):
    bl_idname = 'wm.predict_operator'
    bl_label = 'Predict Operator'
    bl_options = {'REGISTER', 'UNDO'}

    predictions: List[Prediction]
    chosen_prediction: bpy.props.IntProperty(name="Prediction Index", min=0, soft_min=0)

    def execute(self, context):
        # execute operator that user chose
        try:
            chosen_prediction = self.predictions[self.chosen_prediction]
        except IndexError:
            return {'CANCELLED'}
        chosen_prediction.operator.__call__()  # todo handle obligatory arguments
        return {'FINISHED'}

    def invoke(self, context, event):
        # list predictions
        reports = get_operator_reports(context)
        operators = _list_blender_operators()
        self.predictions = predict(context=context.copy(), blender_operators=operators, reports=reports)

        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=500)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'chosen_prediction', text='Chosen')

        col = layout.column()
        for i, p in enumerate(self.predictions):
            row = col.row(align=True)
            row.label(text=f'Prediction {i}:')
            row.label(text=f'bpy.ops.{p.operator.idname_py()}')
