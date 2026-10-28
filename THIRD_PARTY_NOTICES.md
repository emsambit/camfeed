# Third-party assets

- TensorFlow.js 4.22.0: Apache-2.0; `greenwatch/assets/vendor/tf.min.js`. Source: https://github.com/tensorflow/tfjs/tree/tfjs-v4.22.0
- COCO-SSD 2.2.3 and its SSDLite MobileNet V2 model: TensorFlow.js Models / Apache-2.0. Library: `greenwatch/assets/vendor/coco-ssd.min.js`; model JSON/weights: `greenwatch/assets/model/`. Source: https://github.com/tensorflow/tfjs-models/tree/master/coco-ssd . Original model download: https://storage.googleapis.com/tfjs-models/savedmodel/ssdlite_mobilenet_v2/model.json
- Leaflet 1.9.4: BSD-2-Clause; local JS/CSS/images in `greenwatch/assets/vendor/`. Source: https://github.com/Leaflet/Leaflet/tree/v1.9.4
- Bengaluru vector extract: © OpenStreetMap contributors, Open Database Licence (ODbL). https://www.openstreetmap.org/copyright and https://opendatacommons.org/licenses/odbl/1-0/ . Extracted through Overpass; no bulk downloads from public OSM tile servers. The GeoJSON is an adapted database consisting of selected roads/water/localities with rounded coordinates and reduced properties; it is available under ODbL.
- India overview: Natural Earth, public domain. https://www.naturalearthdata.com/about/terms-of-use/ . Country/city data derived from https://github.com/nvkelso/natural-earth-vector . Boundaries are generalized.

Text licences for bundled software are in `licenses/`. Map attribution is also displayed in the interface. The bundled data is a static demo extract, not a current navigation dataset. This file does not relicense pre-existing Camfeed or newly added project source code.
