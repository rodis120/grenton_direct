# Grenton Direct

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

![Project Maintenance][maintenance-shield]

[![Community Forum][forum-shield]][forum]

_Integration to integrate with [grenton][grenton]._

## Installation

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
1. If you do not have a `custom_components` directory (folder) there, you need to create it.
1. In the `custom_components` directory (folder) create a new folder called `grenton_direct`.
1. Download _all_ the files from the `custom_components/grenton_direct/` directory (folder) in this repository.
1. Place the files you downloaded in the new directory (folder) you created.
1. Restart Home Assistant

## Configuration is done in `configutation.yaml`

1. Setup `grenton_direct`

    ```yaml
    grenton_direct:
      ip_address: "< CLU ip address >"
      port: 1234
      key: !secret grenton_key # CLU key extracted from om project file
      iv: !secret grenton_iv # CLU iv extracted from om project file
    ```

1. Configure platforms:

    ```yaml
    switch:
      - platform: "grenton_direct"
        object_id: DOU0947 # grenton object id
        name: Switch

    light:
      - platform: "grenton_direct"
        object_id: "DOU6708" # grenton object id
        name: Center light

      - platform: "grenton_direct"
        object_id: "LED1356" # grenton object id
        name: LED strip

    cover:
      - platform: "grenton_direct"
        object_id: "ROL3875" # grenton object id
        name: Cover Kitchen

    sensor:
      - platform: "grenton_direct"
        object_id: "PAN0453" # grenton object id
        index: 0
        name: Smart panel
        device_class: temperature # optional
        unit_of_measurement: "°C" # optional

    binary_sensor:
      - platform: "grenton_direct"
        object_id: "DIN2341"
        index: 0
        name: "Door sensor"
        device_class: ... # optional 
    ```

## How to get grenton key and iv?

1. Find your project `.omp` file inside `<om directory>/projects`
1. Open your file as zip archive
1. In `properties.xml` you will find section `projectCipherKey`. Example:
    ```xml
    <projectCipherKey id="2">
      <keyBytes id="3">mhcVFwx/y58X6YpHx5seRg==</keyBytes>
      <ivBytes id="4">b15Td53tB6PP4a2HeL2HFw==</ivBytes>
    </projectCipherKey>
    ```
1. Copy and paste your key and iv into `configuration.yaml`

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

***

[grenton_direct]: https://github.com/rodis120/grenton_direct
[commits-shield]: https://img.shields.io/github/commit-activity/y/rodis120/grenton_direct.svg?style=for-the-badge
[commits]: https://github.com/rodis120/grenton_direct/commits/main
[exampleimg]: example.png
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/rodis120/grenton_direct.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-Rogal%20%40rodis120-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/rodis120/grenton_direct.svg?style=for-the-badge
[releases]: https://github.com/rodis120/grenton_direct/releases
[grenton]: https://grenton.com/
