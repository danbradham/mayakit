=======
mayakit
=======

Useful scripts and plugins for Autodesk Maya.


mayakit.plugins
===============
plugins.py adds the plugins folder to MAYA_PLUGIN_PATH and implements the plugins folder as a virtual python package.

 * mayakit.plugins.load_all - load all plugins included in mayakit
 * mayakit.plugins.reload_all - reload all plugins included in mayakit
 * mayakit.plugins.unload_all - unload all plugins included in mayakit
 * mayakit.plugins.safe_load - load a plugin by name
 * mayakit.plugins.safe_unload - unload a plugin by name
 * mayakit.plugins.safe_reload - reload a plugin by name

mayakit.plugins.burnin
----------------------
MPxLocatorNode that draws text in your hud using python string formatting.
Supports vp1 and vp2 drawing with fully configurable font options.

mayakit.plugins.reorderCurve
----------------------------
Reorder the cvs of a nurbsCurve

mayakit.plugins.resampleCurve
-----------------------------
Uniformly resample a nurbsCurve. Essentially the combination of rebuildCurve
and subCurve nodes. The benefit over rebuildCurve is that resampling the curve
does not attempt to maintain curvature and will not suffer from *stray points*
when resampling with lots of points.

mayakit.plugins.pointsOnCurve
-----------------------------
Outputs matrices distributed along a nurbsCurve

mayakit.plugins.textureSampler
------------------------------
Samples a shading network at the specified uv coordinates

mayakit.strands
===============
Utilities and rigs for working with nurbsCurves and hairSystems.
