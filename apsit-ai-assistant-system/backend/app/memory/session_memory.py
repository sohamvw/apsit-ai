sessions = {}

MAX_HISTORY = 6


def add(session_id, data):

    sessions.setdefault(session_id, []).append(data)

    # keep memory small
    if len(sessions[session_id]) > MAX_HISTORY:
        sessions[session_id] = sessions[session_id][-MAX_HISTORY:]


def get(session_id):

    return sessions.get(session_id, [])