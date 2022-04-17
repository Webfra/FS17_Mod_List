import os
from zipfile import ZipFile
from PIL import Image
from io import BytesIO
import base64
import sys

import xml.etree.ElementTree as ET

# ============================================================================
# Folder where the mods are installed to be used by the game.
SAVE_DIR = r'~\Documents\My Games\FarmingSimulator2017\mods'
# Location where the game is installed.
GAME_DIR = r'D:\steam\steamapps\common\Farming Simulator 17'
# Folder where the FS17 mods are stored as backup.
MOD_VAULT = '../Mods'
# Name of the HTML file to create.  A leading underscore ensures it is listed first in Explorer.
OUTPUT_FILE = '_FS7_Mod_List.html'

# ============================================================================
# Constants for HTML generation.
INDENT = ' '    # Intentation to be used.
LINEBR = '\n'   # Linebreak character
FS_GREEN = '#7fc032'
# Size (width and height) of the icons in the HTML.
# All icons will be scaled (up or down) to this size.
IMG_SIZE=128
CSS='''
    body {
        background-color:#1f1f1f;
        color:white;
    }
    table td, table td * {
        vertical-align: top;
    }
    .instDiv {
        background:'''+FS_GREEN+''';
    }
    .fsgreen {
        color:'''+FS_GREEN+''';
    }
    .desc {
        background:#3f3f3f;
        color:white;
    }
'''

# ============================================================================
# main script function to create an HTML overview document of all Mods stored in a folder.
def main():
    # ------------------------------------------------------------------------
    # Get the list of installed Mods. (ZIP files only)
    save_dir = os.path.expanduser(SAVE_DIR)
    installed_mods = []
    if os.path.exists(save_dir):
        installed_mods = get_zipfiles(save_dir)

    # ------------------------------------------------------------------------
    # Get the list of Mods in the current folder.
    list_of_zipfiles = get_zipfiles(MOD_VAULT)
    if len(list_of_zipfiles) <= 0:
        print('***ERROR: No Mods (ZIP files) found in:', os.path.abspath(MOD_VAULT))
        sys.exit(-1)

    # ------------------------------------------------------------------------
    # Start a new HTML file. (Fixed boilerplate code.)
    doc = Html()
    html = doc.tag('html', { 'xmlns':'http://www.w3.org/1999/xhtml' })
    head = html.tag('head')
    head.tag('meta', {'http-equiv':"Content-Type", 'content':"text/html; charset=ISO-8859-1"})
    head.tag('title', text='FS17 Mod List')
    head.tag('style', {'type':'text/css'}, text=CSS)
    body = html.tag('body')
    body.tag('h1', {'class':'fsgreen'}, text='Farming Simulator 17 - Mod List')

    map_mods = []
    other_mods = []

    # ------------------------------------------------------------------------
    # Read MOD information and prepare HTML content.
    num_mods = len(list_of_zipfiles)
    print(f'Reading information for {num_mods} mods...')
    for idx, zipfile in enumerate(list_of_zipfiles):
        # ------------------------------------------------------------------------
        is_installed = zipfile in installed_mods
        # ------------------------------------------------------------------------
        # Show progress.
        # print(idx+1, 'of', len(list_of_zipfiles), zipfile)
        # ------------------------------------------------------------------------
        zipfile_vault = os.path.join(MOD_VAULT, zipfile)
        with ZipFile(zipfile_vault, 'r') as zip:
            # ------------------------------------------------------------------------
            # Read the modDesc.xml file content.
            xml = zip.read('modDesc.xml').decode()
            # ------------------------------------------------------------------------
            # Fix a few issues with the modDesc.xml of some mods.
            # Otherwise, ET.fromstring() will fail!
            # Ampersand is not allowed raw!
            xml = xml.replace(' & ', ' and ')
            # -- is not allowed raw!
            xml = xml.replace('Fill--and', 'Fill-and')
            # Some spaces are missing in some files.
            xml = xml.replace('partOfEconomy="true"', 'partOfEconomy="true" ')
            xml = xml.replace('"configFilename=', '" configFilename=')
            xml = xml.replace('"baleTypesDirectory=', '" baleTypesDirectory=')
            # Some more invalid tokens in Beta mods.
            xml = xml.replace('Bressel&Lade', 'Bressel+Lade')
            xml = xml.replace('and enjoy.]]></de>', 'and enjoy.</de>')
            # ------------------------------------------------------------------------
            # Create an ET Element from the XML.
            modDesc = ET.fromstring(xml, parser=ET.XMLParser(encoding="utf-8"))
            # ------------------------------------------------------------------------
            # Is the mod a Map?
            has_maps = modDesc.find('./maps') is not None
            if has_maps:
                # Maybe in the future, we will treat maps separately...
                pass
            # ------------------------------------------------------------------------
            # Get the Mod title.
            title = get_mod_title(modDesc)
            # ------------------------------------------------------------------------
            # Get the Base64 representation of the icon from the ZIP file.
            icon_b64 = find_icon(zipfile, zip, modDesc)
            # ------------------------------------------------------------------------
            # Get Author name and version
            author = modDesc.find('./author').text
            version = modDesc.find('./version').text
            # ------------------------------------------------------------------------
            # Get the description text of the Mod
            description = modDesc.find('./description')
            description_en = description.find('./en')
            if description_en is not None:
                description = description_en
            description = description.text.strip().replace('\n', '<br>\n')
            # ------------------------------------------------------------------------
            # Is Multiplayer supported?
            multiplayer = False
            MP = modDesc.find('./multiplayer')
            if MP is not None:
                if 'supported' in MP.attrib:
                    multiplayer = MP.attrib['supported'] == 'true'
            # ------------------------------------------------------------------------
            # A new DIV, to contain the Mod description.
            attr = {}
            if is_installed:
                # Mark installed Mods as such.
                attr['class'] = 'instDiv'
            div = Tag('div', attr)
            # ------------------------------------------------------------------------
            # Create a table (with a single row) for the Mod description.
            # 1st column: The Icon
            # 2nd column: Name, version, author, etc.
            # 3rd column: Detailed description text
            tbl = div.tag('table')
            tr = tbl.tag('tr')
            # ------------------------------------------------------------------------
            # 3 Cells for the 3 columns
            td1 = tr.tag('td')
            td2 = tr.tag('td')
            td3 = tr.tag('td', {'class':'desc'} )
            # ------------------------------------------------------------------------
            # Column 1: The image/Icon
            td1.tag('img', { 'src':'data:image/png;base64,' + icon_b64,
                    'width':str(IMG_SIZE), 'height':str(IMG_SIZE) } )
            # ------------------------------------------------------------------------
            # Column 2: Name and information.
            if not is_installed:
                attr = {'class':'fsgreen'}
            else:
                attr = {}
            td2.tag('div', attr ).tag('b', text=f'{title}')  # f'(#{idx+1}) {title}')
            td2.tag('i').tag('small').tag('a', {'href':zipfile}, text=zipfile)
            td2.tag('div', text='Version: ' + version)
            td2.tag('div').tag('small', text='Author: ' + author)
            td2.tag('div').tag('small', text='Installed:' + str(is_installed))
            td2.tag('div').tag('small', text='Multiplayer:' + str(multiplayer))
            # ------------------------------------------------------------------------
            # Column 3: Detailed Mod description
            td3.tag('small', text=description)
            # ------------------------------------------------------------------------
            if has_maps:
                map_mods.append(div)
            else:
                other_mods.append(div)
            # ------------------------------------------------------------------------
    # ------------------------------------------------------------------------
    body.tag('h1', text='Category: Other Mods')
    for div in other_mods:
        body.tag('hr')
        body.add(div)
    # ------------------------------------------------------------------------
    body.tag('hr')
    body.tag('h1', text='Category: Maps')
    for div in map_mods:
        body.tag('hr')
        body.add(div)
    # ------------------------------------------------------------------------
    out_file = os.path.abspath(os.path.join(MOD_VAULT, OUTPUT_FILE))
    print(f'Writing HTML file: {out_file} ...')
    doc.save(out_file)
    # ------------------------------------------------------------------------


# ============================================================================
# Get the title of the mod from the mod description XML.
def get_mod_title(modDesc) -> str:
    desc = 'NONE'
    title = modDesc.find('./title')
    if title is not None:
        desc = title.find('./en')
        if desc is None:
            desc = title.find('./de')
            if desc is None:
                desc = title.find('./fr')
                if desc is None:
                    desc = 'UNKNOWN'
    if type(desc) is not str:
        desc = desc.text
    return  desc


# ============================================================================
# Find the icon
def find_icon(zipfile:str, zip:ZipFile, modDesc) -> str:
    # ------------------------------------------------------------------------
    # Get the icon file
    icon_file = modDesc.find('./iconFilename')
    # Check, if there is a sub-tag "<en>".
    icon_file_en = icon_file.find('./en')
    if icon_file_en is not None:
        icon_file = icon_file_en
    # Get the text of the tag.
    icon_file = icon_file.text
    # Store original name of the icon file, for reporting.
    icon_file_org = icon_file
    # ------------------------------------------------------------------------
    icon_b64 = None
    # ------------------------------------------------------------------------
    while True:
        try:
            icon_b64 = get_icon(zip, icon_file)
        except KeyError:
            # At least one mod has the wrong Icon file name (.png instead of .dds), fix it and try again.
            if icon_file.endswith('.png'):
                icon_file = icon_file.replace('.png', '.dds')
                continue
            # Is the file referring to the Game's store?
            data_store = os.path.join(GAME_DIR, 'data', 'store')
            icon_file = icon_file.replace('$data/store/', data_store+'/')
            if os.path.exists(icon_file):
                continue
            print('Unkown Icon file:', icon_file_org, " in ", zipfile)
            sys.exit(-1)
        break
    # ------------------------------------------------------------------------
    return icon_b64


# ============================================================================
def get_icon(zip, icon_name) -> str:
    try:
        in_bytes = zip.read(icon_name)
    except:
        # Check if the file exists outside the ZIP file.
        # print('Trying to find icon on local storage:', icon_name)
        if os.path.exists(icon_name):
            with open(icon_name, 'rb') as f_in:
                in_bytes = f_in.read()
        else:
            raise KeyError
    with BytesIO(in_bytes) as in_stream:
        image = Image.open(in_stream)
        image = image.resize((IMG_SIZE,IMG_SIZE))
        with BytesIO() as out_stream:
            image.save(out_stream, format='png')
            out_bytes = out_stream.getvalue()
    out_base64 = base64.b64encode(out_bytes).decode()
    return out_base64

# ============================================================================
def get_zipfiles(folder='.'):
    folder = os.path.expanduser(folder)
    for root, _, files in os.walk(folder):
        return [ filename for filename in files if filename.endswith('.zip')]


# ============================================================================
# Tag class to facilitate creating HTML documents.
class Tag(object):
    # ========================================================================
    def __init__(self, name:str, attributes:dict={}, text:str=None) -> None:
        self.name = name
        self.attributes = attributes
        self.text = text
        self.children = []
    # ========================================================================
    def add(self, tag:object) -> None:
        self.children.append(tag)
    # ========================================================================
    def tag(self, name:str, attributes:dict={}, text:str=None) -> object:
        tag = Tag(name, attributes, text)
        self.add(tag)
        return tag
    # ========================================================================
    def to_str(self, indent='') -> str:
        # ------------------------------------------------------------------------
        s =  indent + "<" + self.name
        # ------------------------------------------------------------------------
        if len(self.attributes) > 0:
            for n in sorted(self.attributes):
                s += ' ' + n + '="' + self.attributes[n] + '"'
        # ------------------------------------------------------------------------
        if (self.text is not None) or len(self.children) > 0:
            # ------------------------------------------------------------------------
            s += '>'
            # ------------------------------------------------------------------------
            has_children = len(self.children)>0
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
        super().__init__('html_doc')
    # ========================================================================
    def to_str(self) -> str:
        s = '<?xml version="1.0" encoding="ISO-8859-1" ?>' + LINEBR
        s+= '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">' + LINEBR
        for child in self.children:
            s+= child.to_str()
        return s
    # ========================================================================
    def save(self, filename):
        with open(filename, 'wt', encoding="utf-8", errors="surrogateescape") as f_out:
            f_out.write(self.to_str())


# ============================================================================
if __name__ == '__main__':
    main()


# ============================================================================
# End of file.
# ============================================================================
