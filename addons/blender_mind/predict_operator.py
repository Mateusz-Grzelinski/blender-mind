import bpy
import inspect
from typing import *


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
    # from pprint import pprint, pformat
    # import logging
    # pprint(inspect.getmembers(context))
    # logging.debug(pformat(inspect.getmembers(context)))
    return [Prediction(rank=0.1, operator=bpy.ops.mesh.primitive_plane_add)]


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
