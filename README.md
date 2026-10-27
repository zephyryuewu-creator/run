# Yue Wu · Running Page V1.1

[Open the running dashboard](https://zephyryuewu-creator.github.io/run/)

The original Running Page Dashboard displays Yue's recorded treadmill runs. The component tree, layout, styles, navigation and maps follow upstream. Distance and pace display miles and minutes per mile.

## Update data

Edit Running_Log_EN.xlsx and upload it to this repository with the same name. Pages validates Actual records, regenerates JSON and publishes the site. Example rows are excluded. The importer accepts matching workbooks maintained locally or in Drive; Drive is not the only input.

Initial import: two runs, 20.7 mi, 176 minutes. Missing GPS, heart rate, elevation and start times remain unknown. Personal goals are unset until configured in config.yml.

The current assistant Drive connection permits this import, but does not grant unattended access to GitHub Actions. Upload-based conversion and publication are automatic; unattended private Drive synchronization requires separate runtime authorization.

[中文数据说明](docs/V1.1-DATA.zh-CN.md)

## Development

Install openpyxl==3.1.5, then run python scripts/import_excel.py Running_Log_EN.xlsx before pnpm build. Use pnpm install --frozen-lockfile and pnpm develop to preview.

## Versions and attribution

V1.0 is the original snapshot at b838abd22382d01f6531b3d92fd9705ecb912e10. V1.1 uses personal Excel data and imperial formatting.

Based on [yihong0618/run](https://github.com/yihong0618/run) and [running_page](https://github.com/yihong0618/running_page). Original authors and contributors retain credit. See [MIT LICENSE](LICENSE) and the original [README-CN](README-CN.md).
