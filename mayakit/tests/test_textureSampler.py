

def test_texture_sampler():
    '''Test the texture_sampler function'''

    # Compile and reload plugin modules
    from .. import plugins
    plugins._import_plugins()

    # Get texture_sampler
    from ..plugins.textureSampler import texture_sampler
    from maya import cmds

    cmds.file(new=True, force=True)
    plugins.safe_reload('textureSampler')
    ramp = cmds.shadingNode('ramp', asTexture=True)
    spotlight = cmds.shadingNode('spotLight', asLight=True)

    sampler = texture_sampler(ramp, [(0.5, 0.0), (0.5, 0.5), (0.5, 1.0)])
    sampler.connect('color', [spotlight])
