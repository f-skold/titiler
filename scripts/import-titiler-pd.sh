#!/bin/bash

cp titiler-pds/titiler_pds/routes/[l-s]*.py  titiler/src/titiler/application/titiler/application/routers/
cp titiler-pds/titiler_pds/dependencies.py titiler/src/titiler/core/titiler/core/dependencies_pds.py
cp titiler-pds/titiler_pds/settings.py titiler/src/titiler/core/titiler/core/settings_pds.py
