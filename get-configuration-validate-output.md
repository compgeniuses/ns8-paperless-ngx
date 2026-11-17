# get-configuration Schema

```txt
https://schema.nethserver.org/paperlessngx/get-configuration-validate-output.json
```

Read Paperless configuration; password is always an empty string.

| Abstract            | Extensible | Status         | Identifiable | Custom Properties | Additional Properties | Access Restrictions | Defined In                                                                                                           |
| :------------------ | :--------- | :------------- | :----------- | :---------------- | :-------------------- | :------------------ | :------------------------------------------------------------------------------------------------------------------- |
| Can be instantiated | No         | Unknown status | No           | Forbidden         | Allowed               | none                | [get-configuration-validate-output.json](paperlessngx/get-configuration-validate-output.json "open original schema") |

## get-configuration Type

`object` ([get-configuration](get-configuration-validate-output.md))

# get-configuration Properties

| Property                                                | Type      | Required | Nullable       | Defined by                                                                                                                                                                                                               |
| :------------------------------------------------------ | :-------- | :------- | :------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [paperless_name](#paperless_name)                       | `string`  | Required | cannot be null | [get-configuration](get-configuration-validate-output-properties-paperless_name.md "https://schema.nethserver.org/paperlessngx/get-configuration-validate-output.json#/properties/paperless_name")                       |
| [PAPERLESS_ADMIN_USER](#paperless_admin_user)           | `string`  | Required | cannot be null | [get-configuration](get-configuration-validate-output-properties-paperless_admin_user.md "https://schema.nethserver.org/paperlessngx/get-configuration-validate-output.json#/properties/PAPERLESS_ADMIN_USER")           |
| [PAPERLESS_ADMIN_PASSWORD](#paperless_admin_password)   | `string`  | Required | cannot be null | [get-configuration](get-configuration-validate-output-properties-paperless_admin_password.md "https://schema.nethserver.org/paperlessngx/get-configuration-validate-output.json#/properties/PAPERLESS_ADMIN_PASSWORD")   |
| [PAPERLESS_ADMIN_MAIL](#paperless_admin_mail)           | `string`  | Required | cannot be null | [get-configuration](get-configuration-validate-output-properties-paperless_admin_mail.md "https://schema.nethserver.org/paperlessngx/get-configuration-validate-output.json#/properties/PAPERLESS_ADMIN_MAIL")           |
| [PAPERLESS_TIME_ZONE](#paperless_time_zone)             | `string`  | Required | cannot be null | [get-configuration](get-configuration-validate-output-properties-paperless_time_zone.md "https://schema.nethserver.org/paperlessngx/get-configuration-validate-output.json#/properties/PAPERLESS_TIME_ZONE")             |
| [PAPERLESS_OCR_LANGUAGE](#paperless_ocr_language)       | `string`  | Required | cannot be null | [get-configuration](get-configuration-validate-output-properties-paperless_ocr_language.md "https://schema.nethserver.org/paperlessngx/get-configuration-validate-output.json#/properties/PAPERLESS_OCR_LANGUAGE")       |
| [PAPERLESS_COOKIE_PREFIX](#paperless_cookie_prefix)     | `string`  | Required | cannot be null | [get-configuration](get-configuration-validate-output-properties-paperless_cookie_prefix.md "https://schema.nethserver.org/paperlessngx/get-configuration-validate-output.json#/properties/PAPERLESS_COOKIE_PREFIX")     |
| [PAPERLESS_FILENAME_FORMAT](#paperless_filename_format) | `string`  | Required | cannot be null | [get-configuration](get-configuration-validate-output-properties-paperless_filename_format.md "https://schema.nethserver.org/paperlessngx/get-configuration-validate-output.json#/properties/PAPERLESS_FILENAME_FORMAT") |
| [host](#host)                                           | `string`  | Required | cannot be null | [get-configuration](get-configuration-validate-output-properties-host.md "https://schema.nethserver.org/paperlessngx/get-configuration-validate-output.json#/properties/host")                                           |
| [http2https](#http2https)                               | `boolean` | Required | cannot be null | [get-configuration](get-configuration-validate-output-properties-http2https.md "https://schema.nethserver.org/paperlessngx/get-configuration-validate-output.json#/properties/http2https")                               |
| [lets_encrypt](#lets_encrypt)                           | `boolean` | Required | cannot be null | [get-configuration](get-configuration-validate-output-properties-lets_encrypt.md "https://schema.nethserver.org/paperlessngx/get-configuration-validate-output.json#/properties/lets_encrypt")                           |

## paperless_name



`paperless_name`

* is required

* Type: `string`

* cannot be null

* defined in: [get-configuration](get-configuration-validate-output-properties-paperless_name.md "https://schema.nethserver.org/paperlessngx/get-configuration-validate-output.json#/properties/paperless_name")

### paperless_name Type

`string`

## PAPERLESS_ADMIN_USER



`PAPERLESS_ADMIN_USER`

* is required

* Type: `string`

* cannot be null

* defined in: [get-configuration](get-configuration-validate-output-properties-paperless_admin_user.md "https://schema.nethserver.org/paperlessngx/get-configuration-validate-output.json#/properties/PAPERLESS_ADMIN_USER")

### PAPERLESS_ADMIN_USER Type

`string`

## PAPERLESS_ADMIN_PASSWORD



`PAPERLESS_ADMIN_PASSWORD`

* is required

* Type: `string`

* cannot be null

* defined in: [get-configuration](get-configuration-validate-output-properties-paperless_admin_password.md "https://schema.nethserver.org/paperlessngx/get-configuration-validate-output.json#/properties/PAPERLESS_ADMIN_PASSWORD")

### PAPERLESS_ADMIN_PASSWORD Type

`string`

## PAPERLESS_ADMIN_MAIL



`PAPERLESS_ADMIN_MAIL`

* is required

* Type: `string`

* cannot be null

* defined in: [get-configuration](get-configuration-validate-output-properties-paperless_admin_mail.md "https://schema.nethserver.org/paperlessngx/get-configuration-validate-output.json#/properties/PAPERLESS_ADMIN_MAIL")

### PAPERLESS_ADMIN_MAIL Type

`string`

## PAPERLESS_TIME_ZONE



`PAPERLESS_TIME_ZONE`

* is required

* Type: `string`

* cannot be null

* defined in: [get-configuration](get-configuration-validate-output-properties-paperless_time_zone.md "https://schema.nethserver.org/paperlessngx/get-configuration-validate-output.json#/properties/PAPERLESS_TIME_ZONE")

### PAPERLESS_TIME_ZONE Type

`string`

## PAPERLESS_OCR_LANGUAGE



`PAPERLESS_OCR_LANGUAGE`

* is required

* Type: `string`

* cannot be null

* defined in: [get-configuration](get-configuration-validate-output-properties-paperless_ocr_language.md "https://schema.nethserver.org/paperlessngx/get-configuration-validate-output.json#/properties/PAPERLESS_OCR_LANGUAGE")

### PAPERLESS_OCR_LANGUAGE Type

`string`

## PAPERLESS_COOKIE_PREFIX



`PAPERLESS_COOKIE_PREFIX`

* is required

* Type: `string`

* cannot be null

* defined in: [get-configuration](get-configuration-validate-output-properties-paperless_cookie_prefix.md "https://schema.nethserver.org/paperlessngx/get-configuration-validate-output.json#/properties/PAPERLESS_COOKIE_PREFIX")

### PAPERLESS_COOKIE_PREFIX Type

`string`

## PAPERLESS_FILENAME_FORMAT



`PAPERLESS_FILENAME_FORMAT`

* is required

* Type: `string`

* cannot be null

* defined in: [get-configuration](get-configuration-validate-output-properties-paperless_filename_format.md "https://schema.nethserver.org/paperlessngx/get-configuration-validate-output.json#/properties/PAPERLESS_FILENAME_FORMAT")

### PAPERLESS_FILENAME_FORMAT Type

`string`

## host



`host`

* is required

* Type: `string`

* cannot be null

* defined in: [get-configuration](get-configuration-validate-output-properties-host.md "https://schema.nethserver.org/paperlessngx/get-configuration-validate-output.json#/properties/host")

### host Type

`string`

## http2https



`http2https`

* is required

* Type: `boolean`

* cannot be null

* defined in: [get-configuration](get-configuration-validate-output-properties-http2https.md "https://schema.nethserver.org/paperlessngx/get-configuration-validate-output.json#/properties/http2https")

### http2https Type

`boolean`

## lets_encrypt



`lets_encrypt`

* is required

* Type: `boolean`

* cannot be null

* defined in: [get-configuration](get-configuration-validate-output-properties-lets_encrypt.md "https://schema.nethserver.org/paperlessngx/get-configuration-validate-output.json#/properties/lets_encrypt")

### lets_encrypt Type

`boolean`
