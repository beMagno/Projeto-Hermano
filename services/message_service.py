def generate_message(interview, time_before):
    """
    Gera mensagens personalizadas e humanizadas.
    time_before: 'one_day' ou 'one_hour'
    """
    name = interview['name']
    time = interview['interview_time']
    position = interview['position']

    if time_before == 'one_day':
        return f"Olá {name}, só lembrando que amanhã às {time.split()[1]} você tem uma entrevista com o {position}. Até logo!"
    elif time_before == 'one_hour':
        return f"Olá {name}, passando pra lembrar que às {time.split()[1]} você tem uma entrevista com o {position}, aguardo você."
