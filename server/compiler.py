import pbl
from components import inventory
import traceback

debug_exceptions = False
OK = 'ok'

'''
    Programs are of the form:

    {
        "components": {
            "yfc" : { 
                "_type": "PlaylistSource",
                "name" : "Your Favorite Cofeehouse"
            },

            "tp" : { 
                "_type": "PlaylistSource",
                "name" : "Teen Party"
            },

            "alt" : {
                "_type": "Alternator",
                "source_list" : ["yfc", "tp"]
            },

            "filter": {
                "_type":"AttributeRangeFilter",
                "attr": "audio.energy",
                "max_val" : 0.5,
                "source": "alt"
            },

            "sorter": {
                "_type":"Sorter",
                "attr": "audio.loudness",
                "source": "filter"
            }
        },
        "main": "sorter"
    }
'''

def convert_val_to_type(val, type, program):
    if type in inventory['types']:
        return OK, val
    if type == 'string':
        return OK, str(val)
    elif type == 'string_list':
        return OK, val
    elif type == 'time':
        return OK, val
    elif type == 'optional_date':
        return OK, val
    elif type == 'optional_rel_date':
        return OK, val
    elif type == 'uri':
        return OK, str(val)
    elif type == 'uri_list':
        return OK, val
    elif type == 'number':
        #return OK, float(val)
        return OK, val
    elif type == 'bool':
        return OK, bool(val)
    elif type == 'port':
        if isinstance(val, basestring):
            status, compiled_program = compile_object(val, program)
            return status, compiled_program
        elif isinstance(val, list):
            plist = []
            for name in val:
                status, compiled_program = compile_object(name, program)
                if status == OK:
                    plist.append(compiled_program)
                else:
                    return status, None
            return OK, plist
        else:
            return 'error - bad port type'
            
    elif type == 'source':
        return 'archaic type', type, 'for', val 
        if val:
            status, compiled_program = compile_object(val, program)
            return status, compiled_program
        else:
            return 'error - missing source', val
    elif type == 'source_list':
        return 'archaic type', type, 'for', val 
        plist = []
        for name in val:
            status, compiled_program = compile_object(name, program)
            if status == OK:
                plist.append(compiled_program)
            else:
                return status, None
        return OK, plist
    else:
        return 'unknown type ' + type, None
            

def get_param_val(param, val, spec, program):
    spec_params = spec['params']
    if param in spec_params:
        param_spec = spec_params[param]
        status, outval = convert_val_to_type(val, param_spec['type'], program)
        return status, outval
    else:
        return 'unknown param "' + param + '"', None

def get_spec_by_type(type):
    for component in inventory['components']:
        if type == component['name']:
            return component
    return None
    
def compile_object(objname, program):
    components = program['components']
    symbols = program['symbols']
    hsymbols = program['hsymbols']
    if objname in symbols:
        return OK, symbols[objname]
    else:
        if objname in components:
            comp = components[objname]
            spec = get_spec_by_type(comp['type'])
            if spec:
                params = { }

                for param, val in comp['sources'].items():
                    status, cval = get_param_val(param, val, spec, program)
                    if status == OK:
                        params[param] = cval
                    else:
                        return status + " in " + objname, None

                for param, val in comp['params'].items():
                    status, cval = get_param_val(param, val, spec, program)
                    if status == OK:
                        params[param] = cval
                    else:
                        return status + " in " + objname, None

                try:
                    obj = spec['class'](**params)
                    symbols[objname] = obj
                    hsymbols[obj] = objname
                    return OK, obj
                except pbl.PBLException as e:
                    #traceback.print_exc()
                    print 'e reason', e.reason
                    raise pbl.PBLException(None, e.reason, objname)
                except:
                    traceback.print_exc()
                    if debug_exceptions:
                        raise
                    raise pbl.PBLException(None, "creation failure", objname)
            else:
                return 'unknown type ' + comp['type'] + ' for ' + objname, None
        else:
            return 'missing object ' + str(objname), None
    
def compile(program):
    if 'main' in program and program['main']:
        program['symbols'] = {}
        program['hsymbols'] = {}
        status, compiled_program = compile_object(program['main'], program)
        return status, compiled_program
    else:
        return 'no main', None


if __name__ == '__main__':
    import sys
    import json

    if len(sys.argv) > 1:
        path = sys.argv[1]
        source = open(path).read()
        source_obj = json.loads(source)

        status, obj = compile(source_obj)
        if status == OK:
            print 'compiled! = running'
            pbl.show_source(obj, props= ['src', 'duration'])
        else:
            print 'Whoops', status
