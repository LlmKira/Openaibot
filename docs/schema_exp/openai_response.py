Data = {
    'id': 'chatcmpl-8J2GoGKFhMHc9ZHqUO',
    'object': 'chat.completion',
    'created': 1691547350,
    'model': 'gpt-3.5-turbo-0613',
    'choices': [
        {
            'index': 0,
            'message': {
                'role': 'assistant',
                'content': None,
                'tool_calls': [
                    {
                        'id': 'call_l0a6IzA5KJARPjh7BkHEUe',
                        'type': 'function',
                        'function': {
                            'name': 'set_alarm_reminder',
                            'arguments': '{\n  "delay": 3,\n  "content": "叮铃铃！三分钟已经过去了~"\n}'
                        }
                    }
                ]
            },
            'finish_reason': 'tool_calls'
        }
    ],
    'usage': {
        'prompt_tokens': 198,
        'completion_tokens': 38,
        'total_tokens': 236,
        'pre_token_count': 4096,
        'pre_total': 42,
        'adjust_total': 40,
        'final_total': 2
    }
}
