#	pybeamer - HTML presentation/slide show generator
#	Copyright (C) 2015-2021 Johannes Bauer
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

import enum
from .BaseDirective import BaseDirective

class TOCElement(enum.Enum):
	Chapter = "chapter"
	Section = "section"
	SubSection = "subsection"

class TOCDirective(BaseDirective):
	def __init__(self, toc_element, value):
		assert(isinstance(toc_element, TOCElement))
		self._toc_element = toc_element
		self._value = value

	@property
	def toc_element(self):
		return self._toc_element

	@property
	def value(self):
		return self._value

	def render(self, rendered_presentation):
		if self.toc_element == TOCElement.Chapter:
			rendered_presentation.toc.chapter = self.value
		elif self.toc_element == TOCElement.Section:
			rendered_presentation.toc.section = self.value
		elif self.toc_element == TOCElement.SubSection:
			rendered_presentation.toc.subsection = self.value
		else:
			raise NotImplementedError(self.toc_element)

class TOC():
	def __init__(self):
		pass

	@property
	def chapter(self):
		return self._chapter

	@chapter.setter
	def chapter(self, value):
		self._chapter = value

	@property
	def section(self):
		return self._section

	@section.setter
	def section(self, value):
		self._section = value

	@property
	def subsection(self):
		return self._subsection

	@subsection.setter
	def subsection(self, value):
		self._subsection = value