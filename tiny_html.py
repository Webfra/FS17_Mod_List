from __future__ import annotations

# ============================================================================
INDENT = ' '    # Intentation to be used.
LINEBR = '\n'   # Linebreak character


# ============================================================================
# Tag class to facilitate creating HTML documents.
class Tag(object):
    # ========================================================================
    def __init__(self, name: str, attributes: dict = {}, text: str = None) -> None:
        self.name = name
        self.attributes = attributes
        self.text = text
        self.children = []

    # ========================================================================
    # Add the given tag to the list of sub-tags.
    def add(self, tag: Tag) -> None:
        self.children.append(tag)

    # ========================================================================
    # Create a new sub-tag using the given parameters, add it to the
    # current tag and return it to the caller.
    def tag(self, name: str, attributes: dict = {}, text: str = None) -> object:
        tag = Tag(name, attributes, text)
        self.add(tag)
        return tag

    # ========================================================================
    # Create the default meta tag. Should be used on the <head> tag.
    def default_meta(self):
        self.tag('meta', {'http-equiv': "Content-Type",
                 'content': "text/html; charset=ISO-8859-1"})

    # ========================================================================
    # Convert the Tag to an HTML string.
    def to_str(self, indent='') -> str:
        # ------------------------------------------------------------------------
        s = indent + "<" + self.name
        # ------------------------------------------------------------------------
        if len(self.attributes) > 0:
            for n in sorted(self.attributes):
                s += ' ' + n + '="' + self.attributes[n] + '"'
        # ------------------------------------------------------------------------
        if (self.text is not None) or len(self.children) > 0:
            # ------------------------------------------------------------------------
            s += '>'
            # ------------------------------------------------------------------------
            has_children = len(self.children) > 0
            multi_line = has_children
            # ------------------------------------------------------------------------
            if not multi_line:
                if self.text is not None:
                    if ('\n' in self.text):
                        multi_line = True
            # ------------------------------------------------------------------------
            if multi_line:
                s += LINEBR
            # ------------------------------------------------------------------------
            if self.text is not None:
                if multi_line:
                    s += indent + INDENT
                s += self.text
                if multi_line:
                    s += LINEBR
            # ------------------------------------------------------------------------
            if has_children:
                for child in self.children:
                    s += child.to_str(indent + INDENT)
            # ------------------------------------------------------------------------
            if multi_line:
                s += indent
            s += "</" + self.name
        # ------------------------------------------------------------------------
        else:
            if self.name not in ['br']:
                s += '/'
        # ------------------------------------------------------------------------
        s += '>' + LINEBR
        # ------------------------------------------------------------------------
        return s


# ============================================================================
# HTML class to represent a full HTML document.
class Html(Tag):
    # ========================================================================
    def __init__(self) -> None:
        super().__init__('html', {'xmlns': 'http://www.w3.org/1999/xhtml'})

    # ========================================================================
    def to_str(self) -> str:
        s = '<?xml version="1.0" encoding="ISO-8859-1" ?>' + LINEBR
        s += '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">' + LINEBR
        s += super().to_str()
        return s

    # ========================================================================
    def save(self, filename):
        with open(filename, 'wt', encoding="utf-8", errors="surrogateescape") as f_out:
            f_out.write(self.to_str())


# ============================================================================
# End of file.
# ============================================================================
