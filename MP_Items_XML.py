
import bpy
import os.path
import re
import shutil
import xml.etree.ElementTree as ET
from xml.dom import minidom
from bpy.props import (
    StringProperty,
    BoolProperty,
    PointerProperty,
    CollectionProperty
)
from bpy.types import (
    Panel,
    Operator,
    AddonPreferences,
    PropertyGroup
)
from .MP_Functions import *



class MP_OT_Items_ItemXML_AddPivot(Operator):
    bl_idname = "view3d.addpivot"
    bl_description = "Execute Order 66"
    bl_icon = 'ADD'
    bl_label = "Add a pivot"
        
    def execute(self, context):
        addOrRemovePivot("ADD")
        return {"FINISHED"}
    
    
    
class MP_OT_Items_ItemXML_RemovePivot(Operator):
    bl_idname = "view3d.removepivot"
    bl_description = "Execute Order 66"
    bl_icon = 'ADD'
    bl_label = "Remove a pivot"
        
    def execute(self, context):
        addOrRemovePivot("DEL")
        return {"FINISHED"}
    
    
    
class MP_OT_Items_ItemXML_AddPivot(Operator):
    bl_idname = "view3d.addpivot"
    bl_description = "Execute Order 66"
    bl_icon = 'ADD'
    bl_label = "Add a pivot"
        
    def execute(self, context):
        addOrRemovePivot("ADD")
        return {"FINISHED"}


class MP_PT_Items_ItemXML(Panel):
    # region bl_
    """Creates a Panel in the Object properties window"""
    bl_category = 'ManiaPlanetAddon'
    bl_label = "Item XML"
    bl_idname = "MP_PT_Items_Export_ItemXML"
    bl_parent_id = "MP_PT_Items_Export"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = "objectmode"
    # endregion
    
    @classmethod
    def poll(cls, context):
        mp_props = context.scene.mp_props
        show =  not mp_props.CB_fbx_showConvStatus \
                and not mp_props.LI_fbx_expType == "CONVERT" \
                and mp_props.FI_nadeoIni.endswith("Nadeo.ini")
        return (show)
    
    def draw_header(self, context):
        layout = self.layout
        mp_props = context.scene.mp_props
        row = layout.row()
        row.enabled = True if not mp_props.CB_fbx_showConvStatus else False
        row.prop(mp_props, "CB_xml_genItemXML", text="",)
    
    def draw(self, context):

        layout = self.layout
        mp_props        = context.scene.mp_props
        mp_props_pivots = context.scene.mp_props_pivots
        
        if mp_props.CB_fbx_showConvStatus:
            return
    
        if mp_props.CB_xml_genItemXML is True:
            
            layout.row().prop(mp_props, "ST_xml_author")   
            layout.row().prop(mp_props, "LI_xml_enviType")
            layout.row().prop(mp_props, "LI_xml_itemtype")
            layout.row().prop(mp_props, "LI_xml_waypointtype")
            layout.row().prop(mp_props, "CB_xml_syncGridLevi", icon="UV_SYNC_SELECT")
            
            sync = mp_props.CB_xml_syncGridLevi
            
            boxCol = layout.column(align=True)
            boxRow = boxCol.row(align=True)
            boxRow.enabled = True if sync else False
            boxRow.prop(mp_props, "NU_xml_gridAndLeviX")
            boxRow.prop(mp_props, "NU_xml_gridAndLeviY")
            
            boxCol = layout.column(align=True)
            boxRow = boxCol.row(align=True)
            boxRow.enabled = False if sync else True
            boxRow.prop(mp_props, "NU_xml_gridX")
            boxRow.prop(mp_props, "NU_xml_gridY")
            boxRow = boxCol.row(align=True)
            boxRow.prop(mp_props, "NU_xml_gridXoffset")
            boxRow.prop(mp_props, "NU_xml_gridYoffset")
            
            boxCol = layout.column(align=True)
            boxRow = boxCol.row(align=True)
            boxRow.enabled = False if sync else True
            boxRow.prop(mp_props, "NU_xml_leviX")
            boxRow.prop(mp_props, "NU_xml_leviY")
            boxRow = boxCol.row(align=True)
            boxRow.prop(mp_props, "NU_xml_leviXoffset")
            boxRow.prop(mp_props, "NU_xml_leviYoffset")
            
            boxCol = layout.column(align=True)
            boxRow = boxCol.row(align=True)
            boxRow.prop(mp_props, "CB_xml_ghostMode",   icon="GHOST_DISABLED")
            boxRow.prop(mp_props, "CB_xml_autoRot",     icon="GIZMO")
            boxRow = boxCol.row(align=True)
            boxRow.prop(mp_props, "CB_xml_oneAxisRot",  icon="NORMALS_FACE")
            boxRow.prop(mp_props, "CB_xml_notOnItem",   icon="SNAP_OFF")
            
            layout.separator(factor=spacerFac)
            
            layout.row().prop(mp_props, "CB_xml_pivots",        icon="EDITMODE_HLT")
            
            if mp_props.CB_xml_pivots is True:
                row = layout.row(align=True)
                row.prop(mp_props, "CB_xml_pivotSwitch",    text="Switch")
                row.prop(mp_props, "NU_xml_pivotSnapDis",   text="SnapDist")
                
                row = layout.row(align=True)
                row.operator("view3d.addpivot",    text="Add",       icon="ADD")
                row.operator("view3d.removepivot", text="Delete",    icon="REMOVE")
                # row.operator("view3d.removepivot", text="Del end",   icon="REMOVE")
                
                layout.separator(factor=spacerFac)
                
                for i, pivot in enumerate(mp_props_pivots):
                    boxRow = layout.row(align=True)
                    boxRow.prop(mp_props_pivots[i], "NU_pivotX", text="X" )
                    boxRow.prop(mp_props_pivots[i], "NU_pivotY", text="Y" )
                    boxRow.prop(mp_props_pivots[i], "NU_pivotZ", text="Z" )
                

                    
        layout.separator(factor=spacerFac)



class MP_PT_Items_MeshXML(Panel):
    # region bl_
    """Creates a Panel in the Object properties window"""
    bl_category = 'ManiaPlanetAddon'
    bl_label = "Mesh XML"
    bl_idname = "MP_PT_Items_Export_MeshXML"
    bl_parent_id = "MP_PT_Items_Export"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = "objectmode"
    # endregion
    
    @classmethod
    def poll(cls, context):
        mp_props = context.scene.mp_props
        show =  not mp_props.CB_fbx_showConvStatus \
                and not mp_props.LI_fbx_expType == "CONVERT" \
                and mp_props.FI_nadeoIni.endswith("Nadeo.ini")
        return (show)
    
    def draw_header(self, context):
        layout = self.layout
        mp_props = context.scene.mp_props
        row = layout.row()
        row.enabled = True if not mp_props.CB_fbx_showConvStatus else False
        row.prop(mp_props, "CB_xml_genMeshXML", text="", )
        # layout.scaleY = 2
    
    def draw(self, context):
        layout = self.layout
        mp_props        = context.scene.mp_props
        
        if mp_props.CB_fbx_showConvStatus:
            return
    
        if mp_props.CB_xml_genItemXML is True:
            
            layout.row().prop(mp_props, "LI_xml_enviType")
            layout.row().prop(mp_props, "LI_xml_meshtype")
            row = layout.row(align=False)
            row.label(text="Objscales", icon="EMPTY_ARROWS")
            row.prop(mp_props, "LI_xml_scale", text="")
            row = layout.row(align=False)
            row.label(text="Lightpower", icon="OUTLINER_OB_LIGHT")
            row.prop(mp_props, "LI_xml_powerOfLights", text="")
            
            row = layout.row(align=True)
            row.column().prop(mp_props, "CB_xml_lightglobcolor", )
            row.column().prop(mp_props, "CO_xml_lightglobcolor", text="") if mp_props.CB_xml_lightglobcolor else None
            # row.enabled = True if mp_props.CB_xml_lightglobcolor is True else False
            

        layout.separator(factor=spacerFac)











def getItemXMLData(fbxfilepath: str, waypoint: bool, waypointtype: str) -> dict:
    """generate item xml infos for writing the item xml file"""
    mp_props        = bpy.context.scene.mp_props
    mp_props_pivots = bpy.context.scene.mp_props_pivots
    return {
        "item": {
            "Type":        mp_props.LI_xml_itemtype,
            "Collection":  mp_props.LI_xml_enviType,
            "AuthorName":  mp_props.ST_xml_author ,
        },
        "waypoint": {
            "Type":    mp_props.LI_xml_waypointtype if waypointtype is None else waypointtype
        },
        "triggershape": {
            "File": fbxfilepath.split("/")[-1].replace(".fbx", "Trigger.Shape.gbx"), #yes, no dot
            "Type": "Mesh"
        },
        "moveshape":{
            "File": fbxfilepath.split("/")[-1].replace(".fbx", ".Shape.gbx"),
            "Type": "Mesh"
        },
        "mesh": {
            "File": fbxfilepath.split("/")[-1].replace(".fbx", ".Mesh.gbx"),
        },
        "grid": {
            "HStep":       str(mp_props.NU_xml_gridX),
            "VStep":       str(mp_props.NU_xml_gridY),
            "HOffset":     str(mp_props.NU_xml_gridXoffset),
            "VOffset":     str(mp_props.NU_xml_gridYoffset),
        },
        "levi": {
            "HStep":       str(mp_props.NU_xml_leviX),
            "VStep":       str(mp_props.NU_xml_leviY),
            "HOffset":     str(mp_props.NU_xml_leviXoffset),
            "VOffset":     str(mp_props.NU_xml_leviYoffset),
        },
        "options": {
            "AutoRotation":        str(mp_props.CB_xml_autoRot),
            "ManualPivotSwitch":   str(mp_props.CB_xml_pivotSwitch),
            "NotOnItem":           str(mp_props.CB_xml_notOnItem),
            "OneAxisRotation":     str(mp_props.CB_xml_oneAxisRot),
            
        },
        "pivotsnap": {
            "Distance": str(mp_props.NU_xml_pivotSnapDis),
        },

        "pivots": [
            {"Pos": f"{str(mp_props_pivots[i].NU_pivotX)} {str(mp_props_pivots[i].NU_pivotZ)} {str(mp_props_pivots[i].NU_pivotY)}"}\
                for i, p in enumerate(mp_props_pivots) 
        ]
    }
    #* end getItemXMLData()



def gennerateItemXML(fbxfilepath: str, waypoint: bool, waypointtype: str) -> None:
    """generate item.xml for fbx"""
    
    data        = getItemXMLData(fbxfilepath=fbxfilepath, waypoint=waypoint, waypointtype=waypointtype)
    root        = ET.Element("Item")
    phy         = ET.Element("Phy")
    moveshape   = ET.Element("MoveShape")
    vis         = ET.Element("Vis")
    mesh        = ET.Element("Mesh")
    grid        = ET.Element("GridSnap")
    levi        = ET.Element("Levitation")
    options     = ET.Element("Options")
    pivotsnap   = ET.Element("PivotSnap")
    pivots      = ET.Element("Pivots")
    
    #parenting elements to root
    for el in [phy, vis, mesh, grid, levi, options, pivotsnap, pivots]:
        root.append(el)
    
    #set attributes <a href='test'/>
    root.attrib         = data["item"]
    moveshape.attrib    = data["moveshape"]
    mesh.attrib         = data["mesh"]
    grid.attrib         = data["grid"]
    levi.attrib         = data["levi"]
    options.attrib      = data["options"]
    pivotsnap.attrib    = data["pivotsnap"]
    
    #parenting elements
    phy.append(moveshape)
    vis.append(mesh)
    
    #generate pivot elements
    for pivotPos in data["pivots"]:
        pivot = ET.Element("Pivot")
        pivot.attrib = pivotPos
        pivots.append(pivot)
    
    #cp on condition, convert will fail if set and object isn't a waypoint
    if waypoint and waypointtype != None:
        triggershape= ET.Element("TriggerShape")
        waypoint    = ET.Element("Waypoint")
        triggershape.attrib = data["triggershape"]
        waypoint.attrib     = data["waypoint"]
        phy.append(triggershape)
        root.insert(0, waypoint)
    
    #prettyprint xml and write file
    xmlstr = minidom.parseString(ET.tostring(root)).toprettyxml(indent="    ")
    xmlpath = fbxfilepath.replace(".fbx", ".Item.xml")
    with open(xmlpath, "w") as f:
        f.write(xmlstr)
        f.write("<!-- generated file by the maniaplanet export addon for blender by skyslide -->\n")
    #* end gennerateItemXML()

    

def getMeshXMLData(colname: str) -> dict:
    """generate mesh xml infos """
    mp_props    = bpy.context.scene.mp_props
    colObjs     = bpy.data.collections[colname].all_objects
    
    fixAllMatNames()
    
    meshinfo = {
        "meshparams":{
            "MeshType"      : str(mp_props.LI_xml_meshtype),
            "Collection"    : str(mp_props.LI_xml_enviType),
            "Scale"         : str(1 if mp_props.LI_xml_scale == 0 else mp_props.LI_xml_scale),
        },
        "materials" : [],
        "lights"    : [],
    }
    
    
    for obj in colObjs:
        
        if obj.type == "MESH":
            for mat in obj.data.materials:
                
                if mat.name in [colmat["Name"] for colmat in meshinfo["materials"]]:
                    continue #avoid double mats
                
                if checkMatValidity(matname=mat.name):
                    meshinfo["materials"].append(
                        {
                            "BaseTexture"   : mat["BaseTexture"],
                            "Model"         : mat["Model"],
                            "PhysicsId"     : mat["PhysicsId"],
                            "Name"          : mat.name
                        }
                    )

                
        if obj.type == "LIGHT":
            
            useglobcolor    = mp_props.LI_xml_powerOfLights
            globcolor_r     = mp_props.CO_xml_lightglobcolor.r
            globcolor_g     = mp_props.CO_xml_lightglobcolor.g
            globcolor_b     = mp_props.CO_xml_lightglobcolor.b
            globcolor       = rgbToHEX(globcolor_r,         globcolor_g,        globcolor_b)
            owncolor        = rgbToHEX(obj.data.color.r,    obj.data.color.g,   obj.data.color.b)
            
            meshinfo["lights"].append(
                {
                    "Name"      : str(obj.name),
                    "Type"      : str(obj.data.type),
                    "sRGB"      : str(owncolor) if not useglobcolor else str(globcolor),
                    "Intensity" : str(mp_props.LI_xml_powerOfLights if mp_props.LI_xml_powerOfLights > 0 else 1),
                    "Distance"  : str(obj.data.cutoff_distance),
                }
            )
            
    return meshinfo
    #* end getMeshXMLData()



def gennerateMeshXML(fbxfilepath: str, colname: str) -> None:
    """generate meshparams.xml for fbx"""
    data        = getMeshXMLData(colname=colname)
    root        = ET.Element("MeshParams")
    materials   = ET.Element("Materials")
    lights      = ET.Element("Lights")
    
    #parenting elements to root
    for el in [materials, lights]:
        root.append(el)
    
    #set attributes <a href='test'/>
    root.attrib         = data["meshparams"]

    #generate material elements
    for matdata in data["materials"]:
        mat = ET.Element("Material")
        mat.attrib = matdata
        materials.append(mat)
    
    #generate light elements
    for lightdata in data["lights"]:
        light = ET.Element("Light")
        light.attrib = lightdata
        lights.append(light)
    
    #prettyprint xml and write file
    xmlstr = minidom.parseString(ET.tostring(root)).toprettyxml(indent="    ")
    xmlpath = fbxfilepath.replace(".fbx", ".Meshparams.xml")
    with open(xmlpath, "w") as f:
        f.write(xmlstr)
        f.write("<!-- generated file by the maniaplanet export addon for blender by skyslide -->\n")
    #* end gennerateMeshXML()



def addOrRemovePivot(type: str) -> None:
    """add or remove a pivot for xml creation"""
    mp_props        = bpy.context.scene.mp_props
    mp_props_pivots = bpy.context.scene.mp_props_pivots
    
    pivotcount = len(mp_props_pivots)
    
    if type == "ADD":   mp_props_pivots.add()
    if type == "DEL":   mp_props_pivots.remove(pivotcount -1)
    
        
    













