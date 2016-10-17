import chardet


def decode_text(content):
    """Decode string to unicode string."""
    try:
        charset = chardet.detect(content)['encoding']
        return content.decode(charset)
    except ValueError:
        return ''