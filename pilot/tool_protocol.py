"""Recognise a textual proposal, without executing JSON from prose or examples."""
import json
import re


def textual_call(content,question,names):
    if re.search(r'\b(json|python|javascript|code|syntaxe|api)\b',question,re.I):return False
    def call(value):
        if not isinstance(value,dict):return False
        function=value.get('function',value)
        if isinstance(function,dict) and function.get('name') in names and isinstance(function.get('arguments'),(dict,str)):return True
        calls=value.get('tool_calls')
        return isinstance(calls,list) and any(call(row) for row in calls[:4])
    candidates=[content.strip(),*[match[1] for match in re.finditer(r'```(?:json)?\s*\n([\s\S]*?)```',content,re.I)]]
    for candidate in candidates:
        try:
            if call(json.loads(candidate)):return True
        except (ValueError,TypeError,RecursionError):continue
    return False


def function(call):
    value=call.get('function') if isinstance(call,dict) else None
    return value if isinstance(value,dict) else {}


def presentation(call):
    """A valid history shape for the error result, never repaired execution args."""
    value=function(call);name=value.get('name');arguments=value.get('arguments',{})
    try:
        if isinstance(arguments,str):arguments=json.loads(arguments)
    except (ValueError,TypeError,RecursionError):arguments={}
    result={'type':'function','function':{'name':name if isinstance(name,str) and re.fullmatch(r'[a-zA-Z0-9_]{1,80}',name) else 'unavailable_tool',
                                        'arguments':arguments if isinstance(arguments,dict) else {}}}
    if isinstance(call,dict) and isinstance(call.get('id'),str) and len(call['id'])<=200:result['id']=call['id']
    return result
