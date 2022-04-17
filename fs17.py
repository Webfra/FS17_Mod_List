import xml.etree.ElementTree as ET

import os
from zipfile import ZipFile
from io import BytesIO
import base64

# Pillow Image library (pip install pillow)
from PIL import Image


# ============================================================================
class Mod(object):
    # ========================================================================
    def __init__(self, zipfile: str, GAME_DIR: str, IMG_SIZE: int) -> None:
        # ------------------------------------------------------------------------
        self.GAME_DIR: str = GAME_DIR
        '''The installation folder of the FS17 game.'''
        self.IMG_SIZE: int = IMG_SIZE
        '''The size, to which all icons will be scaled to.'''
        # ------------------------------------------------------------------------
        self.zipfile = zipfile
        '''The name of the ZIP file of the Mod.'''
        self.modDesc = ET.Element('')
        '''The modDesc.xml as xml.etree.ElementTree Element'''
        self.has_maps = False
        '''True, if the Mod contains a map.'''
        self.title = ''
        '''The title of the Mod'''
        self.icon_b64 = ''
        '''Base64 representation of the Mod icon.'''
        self.author = ''
        '''Author of the Mod.'''
        self.version = ''
        '''Version of the Mod.'''
        self.description = ''
        '''Mod description, can be lenghty...'''
        self.multiplayer = False
        '''True, if the Mod claims to support multiplayer.'''
        # ------------------------------------------------------------------------
        self.load()

    # ========================================================================
    def load(self) -> None:
        # ------------------------------------------------------------------------
        with ZipFile(self.zipfile, 'r') as zip:
            # ------------------------------------------------------------------------
            # Read the modDesc.xml file content.
            xml = zip.read('modDesc.xml').decode()
            # ------------------------------------------------------------------------
            # Fix a few issues with the modDesc.xml of some mods.
            # Otherwise, ET.fromstring() will fail!
            xml = Mod.fix_xml(xml)
            # ------------------------------------------------------------------------
            # Create an ET Element from the XML.
            self.modDesc = ET.fromstring(
                xml, parser=ET.XMLParser(encoding="utf-8"))
            # ------------------------------------------------------------------------
            # Is the mod a Map?
            self.has_maps = self.modDesc.find('./maps') is not None
            # ------------------------------------------------------------------------
            # Get the Mod title.
            self.title = self._get_mod_title()
            # ------------------------------------------------------------------------
            # Get the Base64 representation of the icon from the ZIP file.
            self.icon_b64 = self._find_icon(zip)
            # ------------------------------------------------------------------------
            # Get Author name and version
            self.author = self.modDesc.find('./author').text
            self.version = self.modDesc.find('./version').text
            # ------------------------------------------------------------------------
            # Get the description text of the Mod
            description = self.modDesc.find('./description')
            description_en = description.find('./en')
            if description_en is not None:
                description = description_en
            self.description = description.text.strip().replace('\n', '<br>\n')
            # ------------------------------------------------------------------------
            # Is Multiplayer supported?
            self.multiplayer = False
            MP = self.modDesc.find('./multiplayer')
            if MP is not None:
                if 'supported' in MP.attrib:
                    self.multiplayer = MP.attrib['supported'] == 'true'

    # ============================================================================
    # Fix a few issues with the modDesc.xml of some mods.
    # Otherwise, ET.fromstring() will fail!
    @staticmethod
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
    # Find the icon
    def _find_icon(self, zip: ZipFile) -> str:
        # ------------------------------------------------------------------------
        # Get the icon file name.
        icon_file = self.modDesc.find('./iconFilename')
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
        data_store = os.path.join(self.GAME_DIR, 'data', 'store')
        icon_file = icon_file.replace('$data/store/', data_store+'/')
        # ------------------------------------------------------------------------
        while True:
            # ------------------------------------------------------------------------
            try:
                icon_b64 = Mod.get_icon(zip, icon_file, self.IMG_SIZE)
            # ------------------------------------------------------------------------
            except KeyError:
                # ------------------------------------------------------------------------
                # Some mods have the wrong file extension (.png instead of .dds), fix it and try again.
                if icon_file.endswith('.png'):
                    icon_file = icon_file.replace('.png', '.dds')
                    continue
                # ------------------------------------------------------------------------
                # FATAL: Unable to find icon file.
                print('Unkown Icon file:', icon_file_org, " in ", self.zipfile)
                raise KeyError
            break
        # ------------------------------------------------------------------------
        return icon_b64

    # ============================================================================
    @staticmethod
    def get_icon(zip: ZipFile, icon_name: str, IMG_SIZE: int) -> str:
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
    # Get the title of the mod from the mod description XML.
    def _get_mod_title(self) -> str:
        desc = 'NONE'
        title = self.modDesc.find('./title')
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
# End of file.
# ============================================================================
