"""Reassemble bounded journald continuations using their actual stream binding."""

import json


def reassemble(lines):
    pending={};rows=[];errors=[]
    for number,line in enumerate(lines,1):
        try:
            row=json.loads(line)
            key=(row.get('_SYSTEMD_INVOCATION_ID'),row.get('_STREAM_ID'),row.get('_PID'))
            text=row.get('MESSAGE','')
            if not isinstance(text,str):raise ValueError('non-text journal message')
            first,previous=pending.pop(key,(row,''))
            text=previous+text
            if len(text)>1024*1024:raise ValueError('oversized continuation')
            if row.get('_LINE_BREAK')=='line-max':
                if not all(key):raise ValueError('unbound continuation')
                if len(pending)>=16:raise ValueError('too many streams')
                pending[key]=(first,text)
                continue
            first=dict(first,MESSAGE=text)
            first.pop('_LINE_BREAK',None)
            rows.append(first)
        except (ValueError,TypeError) as error:errors.append(dict(line=number,error=str(error)))
    for key in pending:errors.append(dict(error='incomplete_journal_continuation',stream=list(key)))
    return rows,errors


def performance_lines(rows):
    for row in rows:
        message=row.get('MESSAGE','')
        if 'restricted_performance_' in message[:100]:yield json.dumps(row)
