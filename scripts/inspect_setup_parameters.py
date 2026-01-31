"""
Minimal Fusion console script: inspect a single CAM setup parameter in detail.

Usage: run in Fusion "Scripts and Add-Ins". It inspects `DETAILED_PARAM`
on `TARGET_SETUP_NAME`, prints a detailed dump and optionally saves a log.
"""

import adsk.core, adsk.fusion, adsk.cam, traceback, os, datetime

TARGET_SETUP_NAME = 'Setup1'
DETAILED_PARAM = 'wcs_origin_point'
SAVE_DETAIL_LOG = True


def unwrap_value(value, depth=0):
    """Return tuple (leaf_type, leaf_value_or_None_or_'Cast Error')."""
    if value is None:
        return ('NoneType', None)

    try:
        cadPV = adsk.cam.CadObjectParameterValue.cast(value)
        if cadPV:
            v = cadPV.value
            if hasattr(v, 'size'):
                try:
                    size = v.size()
                except Exception:
                    return ('CadObjectCollection', 'Cast Error')
                if size == 0:
                    return ('CadObjectCollection', None)
                return unwrap_value(v[0], depth+1)
            else:
                return unwrap_value(v, depth+1)

        choice = adsk.cam.ChoiceParameterValue.cast(value)
        if choice:
            return ('ChoiceParameterValue', getattr(choice, 'value', ''))

        boolean = adsk.cam.BooleanParameterValue.cast(value)
        if boolean:
            return ('BooleanParameterValue', boolean.value)

        integer = adsk.cam.IntegerParameterValue.cast(value)
        if integer:
            return ('IntegerParameterValue', integer.value)

        double = adsk.cam.DoubleParameterValue.cast(value)
        if double:
            return ('DoubleParameterValue', double.value)

        string = adsk.cam.StringParameterValue.cast(value)
        if string:
            return ('StringParameterValue', string.value)

        point = adsk.core.Point3D.cast(value)
        if point:
            return ('Point3D', {'x': point.x, 'y': point.y, 'z': point.z})

        # BRepVertex (a selected vertex reference)
        vertex = adsk.fusion.BRepVertex.cast(value)
        if vertex:
            try:
                geom = vertex.geometry
                return ('BRepVertex', {'point': (geom.x, geom.y, geom.z)})
            except Exception:
                return ('BRepVertex', 'Cast Error')

        vector = adsk.core.Vector3D.cast(value)
        if vector:
            return ('Vector3D', {'x': vector.x, 'y': vector.y, 'z': vector.z})

        edge = adsk.fusion.BRepEdge.cast(value)
        if edge:
            try:
                sv = edge.startVertex.geometry
                ev = edge.endVertex.geometry
                return ('BRepEdge', {'start': (sv.x, sv.y, sv.z), 'end': (ev.x, ev.y, ev.z)})
            except Exception:
                return ('BRepEdge', 'Cast Error')

        face = adsk.fusion.BRepFace.cast(value)
        if face:
            try:
                centroid = adsk.core.Point3D.cast(face.centroid)
                if centroid:
                    return ('BRepFace', {'centroid': (centroid.x, centroid.y, centroid.z)})
                else:
                    return ('BRepFace', 'No centroid')
            except Exception:
                return ('BRepFace', 'Cast Error')

        body = adsk.fusion.BRepBody.cast(value)
        if body:
            try:
                bbox = body.boundingBox
                if bbox:
                    cx = (bbox.minPoint.x + bbox.maxPoint.x) / 2.0
                    cy = (bbox.minPoint.y + bbox.maxPoint.y) / 2.0
                    cz = (bbox.minPoint.z + bbox.maxPoint.z) / 2.0
                    return ('BRepBody', {'bbox_center': (cx, cy, cz)})
            except Exception:
                return ('BRepBody', 'Cast Error')

        occ = adsk.fusion.Occurrence.cast(value)
        if occ:
            return ('Occurrence', occ.name if hasattr(occ, 'name') else 'Occurrence')

        comp = adsk.fusion.Component.cast(value)
        if comp:
            return ('Component', comp.name if hasattr(comp, 'name') else 'Component')

        if hasattr(value, 'size'):
            try:
                size = value.size()
            except Exception:
                return ('Collection', 'Cast Error')
            if size == 0:
                return ('Collection', None)
            try:
                return unwrap_value(value[0], depth+1)
            except Exception:
                return ('Collection', 'Cast Error')

        if hasattr(value, 'value'):
            try:
                inner = value.value
                if isinstance(inner, (int, float, str, bool)) or inner is None:
                    return (type(inner).__name__, inner)
                return unwrap_value(inner, depth+1)
            except Exception:
                return ('UnknownWithValueAttr', 'Cast Error')

        try:
            s = str(value)
            return ('str', s)
        except Exception:
            return ('Unknown', 'Cast Error')

    except Exception:
        return ('Cast Error', 'Cast Error')
def inspect_param_detail(setup, param_name, save=False):
    """Detailed inspection of a single parameter on `setup`.

    Returns list of lines and optionally writes a timestamped log file.
    """
    lines = []
    app = adsk.core.Application.get()
    ui = app.userInterface

    # locate parameter
    param = None
    try:
        param = setup.parameters.itemByName(param_name)
    except Exception:
        for p in setup.parameters:
            if p.name == param_name:
                param = p
                break

    if not param:
        msg = f"Parameter '{param_name}' not found on setup {setup.name}"
        lines.append(msg)
        print(msg)
        return lines

    lines.append(f"Detailed inspect of param '{param_name}' (setup: {setup.name})")

    # read parameter value
    try:
        pval = param.value
        lines.append(f"  param.objectType: {getattr(pval, 'objectType', type(pval).__name__)}")
    except Exception:
        tb = traceback.format_exc()
        lines.append('  ERROR reading param.value: ' + tb)
        if save:
            _write_log(lines, param_name)
        for l in lines:
            print(l)
        return lines

    # If it's a CadObjectParameterValue, inspect its contents
    cadPV = None
    try:
        cadPV = adsk.cam.CadObjectParameterValue.cast(pval)
    except Exception:
        cadPV = None

    if cadPV:
        try:
            v = cadPV.value
            if hasattr(v, 'size'):
                try:
                    sz = v.size()
                except Exception:
                    lines.append('  CadObjectParameterValue.value: Cast Error when calling size()')
                    if save:
                        _write_log(lines, param_name)
                    for l in lines:
                        print(l)
                    return lines

                lines.append(f'  CadObjectCollection size: {sz}')
                if sz == 0:
                    lines.append('  CadObjectCollection is empty')
                else:
                    for i in range(sz):
                        try:
                            entry = v[i]
                            try:
                                etype, eval_ = unwrap_value(entry)
                                lines.append(f'    entry[{i}] -> {etype}: {repr(eval_)}')
                            except Exception:
                                tb = traceback.format_exc()
                                lines.append(f'    entry[{i}] -> Cast Error:')
                                lines.append('      traceback: ' + tb)
                                try:
                                    lines.append('      repr: ' + repr(entry))
                                except Exception:
                                    lines.append('      repr: <failed>')
                                try:
                                    lines.append('      type: ' + str(type(entry)))
                                except Exception:
                                    lines.append('      type: <failed>')
                                try:
                                    ot = getattr(entry, 'objectType', None)
                                    lines.append('      objectType attr: ' + str(ot))
                                except Exception:
                                    lines.append('      objectType attr: <failed>')
                                try:
                                    ct = getattr(entry, 'classType', None)
                                    lines.append('      classType attr/callable: ' + str(ct))
                                except Exception:
                                    lines.append('      classType attr: <failed>')
                                try:
                                    attrs = dir(entry)
                                    small = ', '.join([a for a in attrs if not a.startswith('_')][:40])
                                    lines.append('      attrs (sample): ' + small)
                                except Exception:
                                    lines.append('      attrs: <failed>')
                        except Exception:
                            lines.append(f'    entry[{i}] -> Cast Error:\n{traceback.format_exc()}')
            else:
                try:
                    etype, eval_ = unwrap_value(v)
                    lines.append(f'  CadObjectParameterValue.value -> {etype}: {repr(eval_)}')
                except Exception:
                    tb = traceback.format_exc()
                    lines.append('  CadObjectParameterValue.value -> Cast Error:')
                    lines.append('    traceback: ' + tb)
                    try:
                        lines.append('    repr: ' + repr(v))
                    except Exception:
                        lines.append('    repr: <failed>')
                    try:
                        lines.append('    type: ' + str(type(v)))
                    except Exception:
                        lines.append('    type: <failed>')
                    try:
                        ot = getattr(v, 'objectType', None)
                        lines.append('    objectType attr: ' + str(ot))
                    except Exception:
                        lines.append('    objectType attr: <failed>')
        except Exception:
            lines.append('  CadObjectParameterValue handling error:\n' + traceback.format_exc())
    else:
        try:
            leaf_type, leaf_val = unwrap_value(pval)
            lines.append(f'  unwrap -> {leaf_type}: {repr(leaf_val)}')
        except Exception:
            lines.append('  unwrap_value failed:\n' + traceback.format_exc())

        try:
            lines.append('  repr: ' + repr(pval))
        except Exception:
            pass

        try:
            attrs = dir(pval)
            small = ', '.join([a for a in attrs if not a.startswith('_')][:20])
            lines.append('  attrs (sample): ' + small)
        except Exception:
            pass

    if save:
        _write_log(lines, param_name)

    for l in lines:
        print(l)
    return lines


def _write_log(lines, param_name):
    try:
        base = os.path.dirname(__file__) if '__file__' in globals() else os.getcwd()
        ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        fname = os.path.join(base, f'inspect_{param_name}_{ts}.log')
        with open(fname, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        print(f'Wrote detailed log to: {fname}')
    except Exception:
        print('Failed to write log: ' + traceback.format_exc())


def run(context):
    app = adsk.core.Application.get()
    ui = app.userInterface
    try:
        doc = app.activeDocument
        cam = adsk.cam.CAM.cast(doc.products.itemByProductType('CAMProductType'))
        if not cam:
            ui.messageBox('No CAM product in active document')
            return

        # find target setup
        target = None
        if TARGET_SETUP_NAME:
            for s in cam.setups:
                if s.name == TARGET_SETUP_NAME:
                    target = s
                    break
        if not target:
            if cam.setups.count > 0:
                target = cam.setups.item(0)
            else:
                ui.messageBox('No setups found')
                return

        # Only run detailed inspect of the configured parameter
        if DETAILED_PARAM:
            inspect_param_detail(target, DETAILED_PARAM, save=SAVE_DETAIL_LOG)
        else:
            print('DETAILED_PARAM not set; nothing to do')

    except Exception:
        ui.messageBox('Failed: {}'.format(traceback.format_exc()))


# Allow running as script from console
if __name__ == '__main__':
    try:
        run(None)
    except Exception:
        print('Error running script: ' + traceback.format_exc())
