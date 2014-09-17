#!/bin/bash

echo "# All good cases should say 'validates'"
for xml in *_ex*.xml; do
  echo -n "xsd: "
  xmllint --noout --schema image-api.xsd $xml
  echo -n "rng: "
  xmllint --noout --relaxng image-api.rng $xml
done

echo "# All bad cases should say 'fails to validate'"
for xml in *bad*xml; do
  echo -n "xsd: "
  xmllint --noout --schema image-api.xsd $xml  2>&1 | grep -v "Schemas validity error"
  echo -n "rng: "
  xmllint --noout --relaxng image-api.rng $xml  2>&1 | grep -v "Relax-NG validity error"
done

