MAX_MSG_LENGTH = 4096
MAX_CAPTION_LENGTH = 1024


def split_message(msg: str, *, with_photo: bool = False) -> list[str]:
    """Splits message into several parts considering telegram limits."""
    parts = []
    while msg:
        # Determine max message length based on
        # `with_photo` and is this the first iteration
        # (we send photo only with first message).
        if parts:
            max_msg_length = MAX_MSG_LENGTH
        else:
            if with_photo:
                max_msg_length = MAX_CAPTION_LENGTH
            else:
                max_msg_length = MAX_MSG_LENGTH

        if len(msg) <= max_msg_length:
            # Message length fits max message length.
            parts.append(msg)
            break
        else:
            # Cut max message length from `msg`
            # and find new line to cut with it.
            part = msg[:max_msg_length]
            first_ln = part.rfind("\n")

            if first_ln != -1:
                # We found new line. Cut with it excluding it.
                new_part = part[:first_ln]
                parts.append(new_part)
                # Cut `msg` with new part length
                # and also remove new line.
                msg = msg[first_ln + 1 :]
            else:
                # We didn't find any new line in message part.
                # Let's try to find at least space to cut with it.
                first_space = part.rfind(" ")

                if first_space != -1:
                    # We found space. Cut with it excluding it.
                    new_part = part[:first_space]
                    parts.append(new_part)
                    # Cut `msg` with new part length
                    # and also remove space.
                    msg = msg[first_space + 1 :]
                else:
                    # We didn't find any space break.
                    # Just append new part and cut message
                    # with part's length.
                    parts.append(part)
                    msg = msg[max_msg_length:]

    return parts
