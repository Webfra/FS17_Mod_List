"""Very simple helper classes for creation of HTML documents."""

from __future__ import annotations

# ============================================================================
INDENT = ' '    # Intentation to be used.
LINEBR = '\n'   # Linebreak character


# ============================================================================
class Tag(object):
    """Class to facilitate creating tags for HTML documents."""

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
    def tag(self, name: str, attributes: dict = {}, text: str = None) -> Tag:
        tag = Tag(name, attributes, text)
        self.add(tag)
        return tag

    # ========================================================================
    # Convert the Tag to an HTML string.
    def html(self, indent='') -> str:
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
                    s += child.html(indent + INDENT)
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
class Html(Tag):
    """Class representing a HTML document."""

    # ========================================================================
    def __init__(self, create_head_and_body=True, charset='utf-8') -> None:
        # ------------------------------------------------------------------------
        super().__init__('html', {'lang': 'en'})
        # ------------------------------------------------------------------------
        self.charset = charset
        # ------------------------------------------------------------------------
        # Set preamble variable now. 
        # The user can overwrite it afterwards, if they want to.
        self.preamble = '<!doctype html>' + LINEBR
        # ------------------------------------------------------------------------
        if create_head_and_body:
            self.head = super().tag('head')
            self.head.tag('meta', { 'charset':self.charset})
            self.body = super().tag('body')
        # ------------------------------------------------------------------------

    # ========================================================================
    def html(self) -> str:
        return self.preamble + super().html()

    # ========================================================================
    def save(self, filename):
        with open(filename, 'wt', encoding=self.charset, errors="surrogateescape") as f_out:
            f_out.write(self.html())


# ============================================================================
# End of file.
# ============================================================================
