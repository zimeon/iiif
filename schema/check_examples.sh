#!/bin/bash

echo "# All good cases should say 'valididates'"
for xml in *_ex*.xml
  do xmllint --noout --schema image-api.xsd $xml
done

echo "# All bad cases should say 'fails to validate'"
for xml in *bad*xml
  do xmllint --noout --schema image-api.xsd $xml  2>&1 | grep -v "Schemas validity error"
done

