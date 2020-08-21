import bpy
import os
import bpy.utils.previews
from bpy.props import *
from bpy.types import (
    Panel,
    Operator,
    AddonPreferences,
    PropertyGroup
)

from . import MP_Functions
from . import MP_Properties
from . import MP_Help
from . import MP_Materials_Create
from . import MP_Icon_Create
from . import MP_Items_Export
from . import MP_Items_XML
from . import MP_Items_Import

bl_info = {
    "name" : "ManiaPlanetAddon",
    "author" : "skyslide & maxi031",
    "description" : "Export collections, generate XMLs, import mats from xmls, convert items, all u nedd boi",
    "blender" : (2, 83, 0),
    "version" : (0, 1, 1),
    "location" : "View3D",
    "warning" : "",
    "category" : "Generic"
}                    


#order matters for UI
classes = (
    MP_Help.MP_PT_Help,
    MP_Help.MP_OT_Help_OpenDocumentation,
    MP_Help.MP_OT_Help_OpenBugreports,
    MP_Help.MP_OT_Help_OpenAssetFolder,
    MP_Help.MP_OT_Help_OpenWorkItemsFolder,
    MP_Help.MP_OT_Help_OpenItemsFolder,
    MP_Help.MP_OT_Help_CreateAssetFolderContent,
 
    MP_Materials_Create.MP_PT_Materials_Create,
    MP_Materials_Create.MP_OT_Materials_Create,
    MP_Materials_Create.MP_OT_Materials_Update,
    
    MP_Icon_Create.MP_PT_Icons,
    MP_Icon_Create.MP_OT_Icon_Create,
    MP_Icon_Create.MP_OT_Icon_Create_Test,
    
    MP_Items_Export.MP_PT_Items_Export,
    MP_Items_Export.MP_OT_Items_Export_ExportAndOrConvert,
    MP_Items_Export.MP_OT_Items_Export_OpenConvertReport,
    
    MP_Items_Import.MP_PT_Items_Import,
    MP_Items_Import.MP_OT_Items_Import,
    MP_Items_Import.MP_OT_Items_Regex,
    
    MP_Items_XML.MP_PT_Items_ItemXML,
    MP_Items_XML.MP_PT_Items_MeshXML,
    MP_Items_XML.MP_OT_Items_ItemXML_AddPivot,
    MP_Items_XML.MP_OT_Items_ItemXML_RemovePivot,
    
    
 
    MP_Properties.MP_Properties_Generated,
    MP_Properties.MP_Properties_Pivots,
    MP_Properties.MP_Properties_for_Panels,
    
    MP_Properties.MP_ItemConvertStatus
)






def register():

    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.mp_props            = PointerProperty(   type=MP_Properties.MP_Properties_for_Panels)
    bpy.types.Scene.mp_props_pivots     = CollectionProperty(type=MP_Properties.MP_Properties_Pivots)
    bpy.types.Scene.mp_props_generated  = CollectionProperty(type=MP_Properties.MP_Properties_Generated)
    bpy.types.Scene.mp_itemconvert      = CollectionProperty(type=MP_Properties.MP_ItemConvertStatus)
    


def unregister():
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.mp_props
    del bpy.types.Scene.mp_props_generated
    del bpy.types.Scene.mp_props_pivots
    del bpy.types.Scene.mp_itemconvert
    
    for pcoll in MP_Functions.preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    
    MP_Functions.preview_collections.clear()


