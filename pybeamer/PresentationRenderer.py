#	pybeamer - HTML presentation/slide show generator
#	Copyright (C) 2021-2021 Johannes Bauer
#
#	This file is part of pybeamer.
#
#	pybeamer is free software; you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation; this program is ONLY licensed under
#	version 3 of the License, later versions are explicitly excluded.
#
#	pybeamer is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with pybeamer; if not, write to the Free Software
#	Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#	Johannes Bauer <JohannesBauer@gmx.de>

import os
import json
import contextlib
from .RendererCache import RendererCache
from .TOC import TOC
from .Exceptions import FailedToLookupFileException
from pybeamer.renderer.LatexFormulaRenderer import LatexFormulaRenderer
from pybeamer.renderer.ImageRenderer import ImageRenderer
import mako.lookup

class RenderedPresentation():
	def __init__(self, renderer, deploy_directory):
		self._renderer = renderer
		self._rendered_slides = [ ]
		self._css = set()
		self._toc = TOC()
		self._deploy_directory = deploy_directory
		self._added_files = set()

	@property
	def renderer(self):
		return self._renderer

	@property
	def rendered_slides(self):
		return iter(self._rendered_slides)

	@property
	def css(self):
		return iter(self._css)

	def add_css(self, filename):
		return self._css.add(filename)

	@property
	def toc(self):
		return self._toc

	def append_slide(self, rendered_slide):
		self._rendered_slides.append(rendered_slide)

	def add_file(self, destination_relpath, content):
		if destination_relpath in self._added_files:
			return
		self._added_files.add(destination_relpath)
		filename = self._deploy_directory + "/" + destination_relpath
		dirname = os.path.dirname(filename)
		with contextlib.suppress(FileExistsError):
			os.makedirs(dirname)
		with open(filename, "w" if isinstance(content, str) else "wb") as f:
			f.write(content)

	def copy_file(self, source_filename, destination_relpath):
		if destination_relpath in self._added_files:
			return
		with open(source_filename, "rb") as f:
			self.add_file(destination_relpath, f.read())

	def copy_template_file(self, template_filename, destination_relpath):
		return self.copy_file(self._renderer.lookup_template_file(template_filename), destination_relpath)

class PresentationRenderer():
	def __init__(self, presentation, rendering_params):
		self._rendered_slides = [ ]
		self._presentation = presentation
		self._rendering_params = rendering_params
		self._custom_renderers = {
			"latex":	RendererCache(LatexFormulaRenderer()),
			"img":		RendererCache(ImageRenderer()),
		}
		self._lookup = mako.lookup.TemplateLookup(list(self._get_mako_lookup_directories()), strict_undefined = True, input_encoding = "utf-8")
		with open(self.lookup_template_file(self._rendering_params.template_style + "/configuration.json")) as f:
			self._template_config = json.load(f)

	def _get_mako_lookup_directories(self):
		for dirname in self._rendering_params.template_dirs:
			yield dirname
			yield dirname + "/" + self._rendering_params.template_style

	@property
	def rendering_params(self):
		return self._rendering_params

	def get_custom_renderer(self, name):
		return self._custom_renderers[name]

	def _search_file(self, filename, search_dirs):
		search_dirs = list(search_dirs)
		for dirname in search_dirs:
			path = dirname + "/" + filename
			if os.path.isfile(path):
				return path
		if len(search_dirs) == 0:
			raise FailedToLookupFileException("No such file: %s (no directories given to look up)" % (filename))
		else:
			raise FailedToLookupFileException("No such file: %s (looked in %s)" % (filename, ", ".join(search_dirs)))

	def lookup_template_file(self, filename):
		return self._search_file(filename, self._rendering_params.template_dirs)

	def lookup_include(self, filename):
		return self._search_file(filename, self._rendering_params.include_dirs)

	def _compute_renderable_slides(self, rendered_presentation):
		renderable_slides = [ ]
		for directive in self._presentation:
			generator = directive.render(rendered_presentation)
			if generator is not None:
				renderable_slides += generator
		return renderable_slides

	def render(self, deploy_directory):
		rendered_presentation = RenderedPresentation(self, deploy_directory = deploy_directory)
		rendered_presentation.copy_template_file("base/pybeamer.js", "pybeamer.js")

		for filename in self._template_config.get("files", { }).get("static", [ ]):
			rendered_presentation.copy_template_file("%s/%s" % (self._rendering_params.template_style, filename), filename)
		for filename in self._template_config.get("files", { }).get("css", [ ]):
			rendered_presentation.copy_template_file("%s/%s" % (self._rendering_params.template_style, filename), filename)
			rendered_presentation.add_css(filename)

		template_args = {
			"renderer":					self,
			"presentation":				self._presentation,
			"rendered_presentation":	rendered_presentation,
		}

		for renderable_slide in self._compute_renderable_slides(rendered_presentation):
			args = dict(template_args)
			args.update({
				"slide":			renderable_slide,
			})
			template = self._lookup.get_template("slide_%s.html" % (renderable_slide.slide_type))
			result = template.render(**args)
			rendered_presentation.append_slide(result)

		for (template_filename, target_filename) in [ ("base/master.html", "index.html"), ("base/pybeamer.css", "pybeamer.css") ]:
			template = self._lookup.get_template(template_filename)
			result = template.render(**template_args)
			rendered_presentation.add_file(target_filename, result)