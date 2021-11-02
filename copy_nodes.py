bl_info = {
    "name": "Copy Math Nodes",
    "description": "copy math nodes from one tree to an other",
    "author": "Syborg64",
    "version": (0, 0, 3),
    "blender": (2, 93, 5),
    "location": "Node Editor > Tools",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Development"
}


from typing import Union
import bpy

from bpy.props import (StringProperty,
                       PointerProperty,
                       FloatProperty
                       )

from bpy.types import (Panel,
                       PropertyGroup,
                       Operator,
                       )


class copy_nodes_props(PropertyGroup):
    source_tree : StringProperty(
        name = "Source NodeTree",
        description = "Name of the source NodeTree : Material, NodeGroup or GeometryNodeTree",
        default = "Material"
    )

    dest_tree : StringProperty(
        name = "Destinnatio NodeTree",
        description = "Name of the destination NodeTree : Material, NodeGroup or GeometryNodeTree",
        default = "Geometry Nodes"
    )

    offset_x : FloatProperty(
        name = "X offset",
        description = "X Offset to be applied when copying the network",
        default = 0
    )

    offset_y : FloatProperty(
        name = "Y offset",
        description = "Y Offset to be applied when copying the network",
        default = 0
    )



class WM_OT_copy_nodes_operator(Operator):
    """Copy a set of compatible math nodes from two different NodeTree types. Either from name or object. Can do material nodetrees, nodegroups or geometry node trees"""
    bl_idname = 'copy_nodes.copy_nodes'
    bl_label = 'Copy math Nodes'

    def execute(self, context):
        scene = context.scene
        props = scene.copy_nodes_props
        self.copy_nodes(props.source_tree, props.dest_tree, [props.offset_x, props.offset_y])
        return {'FINISHED'}

    @staticmethod
    def copy_nodes(tree1,  tree2, offset = [0, 0], mathdict = None):
        #User definable mask for what to attempt to copy. note that most ShaderNode types are illegal
        if mathdict is None:
            mathdict = ["NodeValue", "NodeReroute", "ShaderNodeMath", "ShaderNodeVectorMath", "ShaderNodeCombineXYZ", "ShaderNodeSeparateXYZ", "ShaderNodeCombineRGB", "ShaderNodeSeparateRGB"]
        #
        #either give the NodeTree itself or the string name of the datablock
        print(tree1, tree2)
        print(tree1.__class__)
        if isinstance(tree1, str):
            print("try1")
            tree1 = bpy.data.materials.get(tree1, None) or bpy.data.node_groups.get(tree1, None)
        if isinstance(tree2, str):
            tree2 = bpy.data.materials.get(tree2, None) or bpy.data.node_groups.get(tree2, None)
        if isinstance(tree1, bpy.types.Material):
            tree1 = tree1.node_tree or None
        if isinstance(tree2, bpy.types.Material):
            tree2 = tree2.node_tree or None
        if tree1 is None or tree2 is None:
            print("Copy failed : invalid args")
            return 1
        print(tree1, tree2)
        #
        #Pick all nodes that are the right type and all links connected to the right nodes
        nodes = [node for node in tree1.nodes if node.bl_idname in mathdict]
        links = [link for link in tree1.links if (link.from_node.bl_idname in mathdict or link.to_node.bl_idname in mathdict)]
        #
        #Copy all nodes and their attributes. Probably missing a lot
        for onode in nodes:
            nnode = tree2.nodes.new(onode.bl_idname)
            nnode.location = [onode.location[0] + offset[0], onode.location[1] + offset[1]]
            nnode.name = onode.name
            try:
                nnode.operation = onode.operation
            except AttributeError:
                pass
            for i, input in enumerate(onode.inputs):
                nnode.inputs[i].default_value = input.default_value
        #
        #Recreate all links
        for olink in links:
            ofs = olink.from_socket
            ots = olink.to_socket

            try:
                nfromsocket = [ i for i in tree2.nodes[ofs.node.name].outputs if i.identifier == ofs.identifier][0]
            except (IndexError, KeyError):
                reroute = tree2.nodes.new("NodeReroute")
                tree2.nodes.new("NodeFrame").location = [ofs.node.location[0] + offset[0], ofs.node.location[1] + offset[1]]
                reroute.location = [ofs.node.location[0] + offset[0] + 75, ofs.node.location[1] + offset[1] - 50]
                nfromsocket = reroute.outputs[0]
            try:
                ntosocket = [ i for i in tree2.nodes[ots.node.name].inputs if i.identifier == ots.identifier][0]
            except (IndexError, KeyError):
                reroute = tree2.nodes.new("NodeReroute")
                tree2.nodes.new("NodeFrame").location = [ofs.node.location[0] + offset[0], ofs.node.location[1] + offset[1]]
                reroute.location = [ofs.node.location[0] + offset[0] + 75, ofs.node.location[1] + offset[1] - 50]
                ntosocket = reroute.outputs[0]
            nlink = tree2.links.new(nfromsocket, ntosocket)
        print("copy finished")
        return 0


class OBJECT_PT_copy_nodes_panel(Panel):
    bl_idname = 'OBJECT_PT_copy_nodes_panel'
    bl_label = 'Copy math Nodes'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Copy Nodes'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.copy_nodes_props

        layout.prop(props, "source_tree")
        layout.prop(props, "dest_tree")
        layout.prop(props, "offset_x")
        layout.prop(props, "offset_y")
        layout.operator('copy_nodes.copy_nodes', text='Copy')

classes = (
    WM_OT_copy_nodes_operator,
    OBJECT_PT_copy_nodes_panel
)

def register():
    from bpy.utils import register_class
    register_class(copy_nodes_props)
    bpy.types.Scene.copy_nodes_props = PointerProperty(type=copy_nodes_props)

    for cls in classes:
        print("registering", cls)
        register_class(cls)
        print("registered", cls)


def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

    del bpy.types.Scene.copy_nodes_props



if __name__ == '__main__':
    register()
