#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2018 Ayuntamiento de Santiago de Compostela, Entidad Pública Empresarial Red.es
# 
# This file is part of the "Open Data Portal of Santiago de Compostela", developed within the "Ciudades Abiertas" project.
# 
# Licensed under the EUPL, Version 1.2 or - as soon they will be approved by the European Commission - subsequent versions of the EUPL (the "Licence");
# You may not use this work except in compliance with the Licence.
# You may obtain a copy of the Licence at:
# 
# https://joinup.ec.europa.eu/software/page/eupl
# 
# Unless required by applicable law or agreed to in writing, software distributed under the Licence is distributed on an "AS IS" basis,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the Licence for the specific language governing permissions and limitations under the Licence.
 
try:
    # optional fancy progress bar you can install
    from progressbar import ProgressBar, Percentage, Bar, ETA

    class GaProgressBar(ProgressBar):
        def __init__(self, total):
            if total == 0:
                return
            widgets = ['Test: ', Percentage(), ' ', Bar(),
                       ' ', ETA(), ' ']
            ProgressBar.__init__(self, widgets=widgets,
                                 maxval=total)
            self.start()

except ImportError:
    class GaProgressBar(object):
        def __init__(self, total):
            self.total = total

        def update(self, count):
            if count % 100 == 0:
                print '.. %d/%d done so far' % (count, self.total)