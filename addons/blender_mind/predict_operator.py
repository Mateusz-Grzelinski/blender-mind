import logging
from collections import defaultdict

import bpy
import inspect
from typing import *

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s %(pathname)s:%(lineno)d  %(message)s')


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


_operators = {p.idname(): p for p in _list_blender_operators()}
_operators.update({p.idname_py().split('(')[0]: p for p in _list_blender_operators()})


def get_operator(idname: str) -> bpy.types.Operator:
    global _operators
    op = _operators.get(idname)
    if op:
        return op
    _operators = {p.idname(): p for p in _list_blender_operators()}
    _operators.update({p.idname_py().split('(')[0]: p for p in _list_blender_operators()})
    op = _operators.get(idname)
    if op:
        return op
    raise Exception(f'There is no operator called {idname}')


def reports_to_operators(reports: List[str], operators: List[bpy.types.Operator]) -> List[bpy.types.Operator]:
    # todo we can also extract arguments
    ops = []
    for report in reports:
        assert report.startswith('bpy.ops')
        access_path = report.split('(')[0]
        op_name = access_path[len('bpy.ops.'):]
        ops.append(get_operator(op_name))
    return ops


class Prediction:
    def __init__(self, operator: bpy.types.Operator, rating: float, operator_arguments: Dict[str, Any] = None):
        self.operator = operator
        self.rating = rating
        self.operator_arguments = operator_arguments or {}


class MostRecentlyUsedPredictionModel:
    def __init__(self, all_operators: List[bpy.types.Operator], history: List[bpy.types.Operator]):
        self.history = history
        self.all_operators = all_operators

    def predict(self, context: Dict) -> Generator[Prediction, None, None]:
        valid_operators = set()
        the_rest = set()
        for op in self.all_operators:
            if op.poll():
                valid_operators.add(op)
            else:
                the_rest.add(op)

        best_fits = {op.idname(): Prediction(operator=op, rating=0) for op in valid_operators}
        history_idname = [op.idname() for op in self.history]
        # simple frequency based
        for op_idname in best_fits:
            best_fits[op_idname].rating += history_idname.count(op_idname) / 10

        # frequency based, but only after occurrences
        try:
            last_action = self.history[-1]
        except IndexError:
            pass
        else:
            operators_in_history = defaultdict(list)
            for i, op in enumerate(self.history):
                operators_in_history[op.idname()].append(i)

            occurrences = operators_in_history[last_action.idname()]
            for index in occurrences:
                try:
                    next_action = self.history[index + 1]  # can fail on last history element
                    # skip repeated calls
                    if next_action.idname() != last_action.idname():
                        best_fits[next_action.idname()].rating += 1  # can fail on unknown operator
                except IndexError:
                    continue
        for op_idname, prediction in sorted(best_fits.items(), key=lambda item: item[1].rating, reverse=True):
            yield prediction
        for op in the_rest:
            yield Prediction(operator=op, rating=-1)


def predict(context: Dict,
            blender_operators: List[bpy.types.Operator],
            reports: List[str]) -> List[Prediction]:
    """

    :param context: copy of blender context, can be used for checking which operators can be executed: Operator.poll(context)
    :param blender_operators: list of possible operators
    :param reports: history of user actions
    :return: list of predictions
    """
    history = reports_to_operators(reports=reports, operators=blender_operators)
    model = MostRecentlyUsedPredictionModel(all_operators=blender_operators, history=history)
    return list(model.predict(context))


_Identifier = str
_Name = str
_Description = str
_EnumItem = Tuple[_Identifier, _Name, _Description]

predictions = []


# this can be called multiple times, this is only view layer!
def get_enum_operators_callback(self: "WM_OT_predict_operator", context) -> List[_EnumItem]:
    enum_predictions = []
    for pred in predictions:
        t = pred.operator.get_rna_type()
        if t.name:
            name = f'{t.name} ({pred.rating}) {pred.operator.idname_py()}'
        else:
            name = f'{pred.operator.idname_py()} ({pred.rating})'
        enum_predictions.append((t.identifier, name, t.description))
    return enum_predictions


class WM_OT_predict_operator(bpy.types.Operator):
    bl_idname = 'wm.predict_operator'
    bl_label = 'Predict Operator'
    # bl_options = {'REGISTER', 'UNDO'}
    bl_property = 'operators'

    operators: bpy.props.EnumProperty(
        name="List all operators, sorted by relevance",
        items=get_enum_operators_callback,
        options={"SKIP_SAVE", "HIDDEN"}
    )

    # predictions = []  #: List[Prediction]

    def execute(self, context):
        op = get_operator(self.operators)
        global predictions
        del predictions
        predictions = []
        op.__call__()  # todo handle obligatory arguments
        return {'FINISHED'}

    def invoke(self, context, event):
        global predictions
        blender_operators = _list_blender_operators()
        context_copy = context.copy()
        if context_copy:
            blender_operators = [p for p in blender_operators if p.poll()]
        reports = get_operator_reports(context)
        predictions = predict(context=context_copy, blender_operators=blender_operators, reports=reports)

        logging.info(f'Showing predictions for {len(predictions)}/{len(_operators)} operators')
        context.window_manager.invoke_search_popup(self)
        return {'RUNNING_MODAL'}
