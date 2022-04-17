import os
from types import SimpleNamespace
from zipfile import ZipFile
from io import BytesIO
import base64
import sys
import xml.etree.ElementTree as ET

# Pillow Image library (pip install pillow)
from PIL import Image

from tiny_html import Tag, Html

# ============================================================================
# Folder where the mods are installed to be used by the game.
SAVE_DIR = r'~\Documents\My Games\FarmingSimulator2017\mods'
# Location where the game is installed.
GAME_DIR = r'D:\steam\steamapps\common\Farming Simulator 17'
# Folder where the FS17 mods are stored as backup.
MOD_VAULT = r'..\Mods'
# Name of the HTML file to create.  A leading underscore ensures it is listed first in Explorer.
OUTPUT_FILE = '_FS7_Mod_List.html'
# Title of the HTML document.
HTML_TITLE = 'FS17 - Mod List'

# ============================================================================
# Constants for HTML generation.
FS_GREEN = '#7fc032'
# Size (width and height) of the icons in the HTML.
# All icons will be scaled (up or down) to this size.
IMG_SIZE = 128
CSS = '''
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
    print('Finding Mods in', os.path.abspath(MOD_VAULT))
    list_of_zipfiles = get_zipfiles(MOD_VAULT)
    if len(list_of_zipfiles) <= 0:
        print('***ERROR: No Mods (ZIP files) found in:',
              os.path.abspath(MOD_VAULT))
        sys.exit(-1)

    # ------------------------------------------------------------------------
    mods = {'maps': [], 'other': []}

    # ------------------------------------------------------------------------
    # Read MOD information and prepare HTML content.
    num_mods = len(list_of_zipfiles)
    print(f'Reading information for {num_mods} mods...')
    for idx, zipfile in enumerate(list_of_zipfiles):
        # ------------------------------------------------------------------------
        # Show progress.
        # print(idx+1, 'of', len(list_of_zipfiles), zipfile)
        # ------------------------------------------------------------------------
        # Collect information about the mod.
        mod_info = get_mod_info(zipfile, installed_mods)
        # ------------------------------------------------------------------------
        # Create a HTML representation for the mod.
        div = create_mod_html(mod_info)
        # ------------------------------------------------------------------------
        mods['maps' if mod_info.has_maps else 'other'].append(div)

    # ------------------------------------------------------------------------
    doc = create_html_doc(mods)

    # ------------------------------------------------------------------------
    out_file = os.path.abspath(os.path.join(MOD_VAULT, OUTPUT_FILE))
    print(f'Writing HTML file: {out_file} ...')
    doc.save(out_file)
    # ------------------------------------------------------------------------


# ============================================================================
# Create a HTML document from the mods dictionary.
def create_html_doc(mods: dict) -> Html:
    # ------------------------------------------------------------------------
    # Start a new HTML file.
    html = Html()
    # ------------------------------------------------------------------------
    # Create a <head> tag.
    html.head.tag('title', text=HTML_TITLE)
    html.head.tag('style', {'type': 'text/css'}, text=CSS)
    # ------------------------------------------------------------------------
    # Create a <body> tag.
    body = html.body
    body.tag('h1', {'class': 'fsgreen'}, text=HTML_TITLE)
    # ------------------------------------------------------------------------
    # Add all "other" mods.
    body.tag('h1', text='Category: Other Mods')
    for div in mods['other']:
        body.tag('hr')
        body.add(div)
    # ------------------------------------------------------------------------
    # Add all "map" mods.
    body.tag('hr')
    body.tag('h1', text='Category: Maps')
    for div in mods['maps']:
        body.tag('hr')
        body.add(div)
    # ------------------------------------------------------------------------
    return html


# ============================================================================
# Create a HTML representation for the mod.
def create_mod_html(mod: SimpleNamespace) -> Tag:
    # ------------------------------------------------------------------------
    # A new DIV, to contain the Mod description.
    div = Tag('div', {'class': 'instDiv'} if mod.is_installed else {})
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
    td3 = tr.tag('td', {'class': 'desc'})
    # ------------------------------------------------------------------------
    # Column 1: The image/Icon
    td1.tag('img', {'src': 'data:image/png;base64,' + mod.icon_b64,
            'width': str(IMG_SIZE), 'height': str(IMG_SIZE)})
    # ------------------------------------------------------------------------
    # Column 2: Name and information.
    if not mod.is_installed:
        attr = {'class': 'fsgreen'}
    else:
        attr = {}
    # f'(#{idx+1}) {title}')
    td2.tag('div', attr).tag('b', text=f'{mod.title}')
    td2.tag('i').tag('small').tag('a', {'href': mod.zipfile}, text=mod.zipfile)
    td2.tag('div', text='Version: ' + mod.version)
    td2.tag('div').tag('small', text='Author: ' + mod.author)
    td2.tag('div').tag('small', text='Installed:' + str(mod.is_installed))
    td2.tag('div').tag('small', text='Multiplayer:' + str(mod.multiplayer))
    # ------------------------------------------------------------------------
    # Column 3: Detailed Mod description
    td3.tag('small', text=mod.description)
    # ------------------------------------------------------------------------
    return div


# ============================================================================
def get_mod_info(zipfile: str, installed_mods: list) -> SimpleNamespace:
    # ------------------------------------------------------------------------
    mod = SimpleNamespace()
    # ------------------------------------------------------------------------
    mod.zipfile = zipfile
    # ------------------------------------------------------------------------
    mod.is_installed = zipfile in installed_mods
    # ------------------------------------------------------------------------
    mod.zipfile_vault = os.path.join(MOD_VAULT, zipfile)
    # ------------------------------------------------------------------------
    with ZipFile(mod.zipfile_vault, 'r') as zip:
        # ------------------------------------------------------------------------
        # Read the modDesc.xml file content.
        xml = zip.read('modDesc.xml').decode()
        # ------------------------------------------------------------------------
        # Fix a few issues with the modDesc.xml of some mods.
        # Otherwise, ET.fromstring() will fail!
        xml = fix_xml(xml)
        # ------------------------------------------------------------------------
        # Create an ET Element from the XML.
        mod.modDesc = ET.fromstring(xml, parser=ET.XMLParser(encoding="utf-8"))
        # ------------------------------------------------------------------------
        # Is the mod a Map?
        mod.has_maps = mod.modDesc.find('./maps') is not None
        # ------------------------------------------------------------------------
        # Get the Mod title.
        mod.title = get_mod_title(mod.modDesc)
        # ------------------------------------------------------------------------
        # Get the Base64 representation of the icon from the ZIP file.
        mod.icon_b64 = find_icon(zipfile, zip, mod.modDesc)
        # ------------------------------------------------------------------------
        # Get Author name and version
        mod.author = mod.modDesc.find('./author').text
        mod.version = mod.modDesc.find('./version').text
        # ------------------------------------------------------------------------
        # Get the description text of the Mod
        description = mod.modDesc.find('./description')
        description_en = description.find('./en')
        if description_en is not None:
            description = description_en
        mod.description = description.text.strip().replace('\n', '<br>\n')
        # ------------------------------------------------------------------------
        # Is Multiplayer supported?
        mod.multiplayer = False
        MP = mod.modDesc.find('./multiplayer')
        if MP is not None:
            if 'supported' in MP.attrib:
                mod.multiplayer = MP.attrib['supported'] == 'true'
    return mod


# ============================================================================
# Fix a few issues with the modDesc.xml of some mods.
# Otherwise, ET.fromstring() will fail!
def fix_xml(xml: str) -> str:
    # ------------------------------------------------------------------------
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
    return xml


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
    return desc


# ============================================================================
# Find the icon
def find_icon(zipfile: str, zip: ZipFile, modDesc) -> str:
    # ------------------------------------------------------------------------
    # Get the icon file name.
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
    # Is the file referring to the Game's store?
    data_store = os.path.join(GAME_DIR, 'data', 'store')
    icon_file = icon_file.replace('$data/store/', data_store+'/')
    # ------------------------------------------------------------------------
    while True:
        # ------------------------------------------------------------------------
        try:
            icon_b64 = get_icon(zip, icon_file)
        # ------------------------------------------------------------------------
        except KeyError:
            # ------------------------------------------------------------------------
            # Some mods have the wrong file extension (.png instead of .dds), fix it and try again.
            if icon_file.endswith('.png'):
                icon_file = icon_file.replace('.png', '.dds')
                continue
            # ------------------------------------------------------------------------
            # FATAL: Unable to find icon file.
            print('Unkown Icon file:', icon_file_org, " in ", zipfile)
            sys.exit(-1)
        break
    # ------------------------------------------------------------------------
    return icon_b64


# ============================================================================
def get_icon(zip, icon_name) -> str:
    # ------------------------------------------------------------------------
    # Try to read the icon from the zip file.
    try:
        in_bytes = zip.read(icon_name)
    # ------------------------------------------------------------------------
    # Otherwise, try to read the file from local storage
    except:
        # Check if the file exists outside the ZIP file.
        if os.path.exists(icon_name):
            with open(icon_name, 'rb') as f_in:
                in_bytes = f_in.read()
        else:
            raise KeyError
    # ------------------------------------------------------------------------
    # Read the icon image and convert it to a Base64 representation PNG.
    with BytesIO(in_bytes) as in_stream:
        # Open the image using PIL Image.
        image = Image.open(in_stream)
        # Scale the image to standard size.
        image = image.resize((IMG_SIZE, IMG_SIZE))
        # Convert the image.
        with BytesIO() as out_stream:
            # Convert Image to PNG.
            image.save(out_stream, format='png')
            # Convert Image to Base64.
            out_base64 = base64.b64encode(out_stream.getvalue()).decode()
    # ------------------------------------------------------------------------
    return out_base64


# ============================================================================
# Get a list of zip files in the given folder.
def get_zipfiles(folder: str) -> list:
    # ------------------------------------------------------------------------
    # Convert "~" into the users home folder.
    folder = os.path.expanduser(folder)
    # ------------------------------------------------------------------------
    # Get all zip files in folder.
    for _, _, files in os.walk(folder):
        return [filename for filename in files if filename.endswith('.zip')]


# ============================================================================
if __name__ == '__main__':
    main()


# ============================================================================
# End of file.
# ============================================================================
