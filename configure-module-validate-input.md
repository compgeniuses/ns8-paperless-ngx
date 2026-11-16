# configure-module Schema

```txt
https://schema.nethserver.org/paperlessngx/configure-module-validate-input.json
```

Configure paperless

| Abstract            | Extensible | Status         | Identifiable | Custom Properties | Additional Properties | Access Restrictions | Defined In                                                                                                       |
| :------------------ | :--------- | :------------- | :----------- | :---------------- | :-------------------- | :------------------ | :--------------------------------------------------------------------------------------------------------------- |
| Can be instantiated | No         | Unknown status | No           | Forbidden         | Allowed               | none                | [configure-module-validate-input.json](paperlessngx/configure-module-validate-input.json "open original schema") |

## configure-module Type

`object` ([configure-module](configure-module-validate-input.md))

# configure-module Properties

| Property                                                | Type      | Required | Nullable       | Defined by                                                                                                                                                                                                          |
| :------------------------------------------------------ | :-------- | :------- | :------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [paperless_name](#paperless_name)                       | `string`  | Optional | cannot be null | [configure-module](configure-module-validate-input-properties-paperless_name.md "https://schema.nethserver.org/paperlessngx/configure-module-validate-input.json#/properties/paperless_name")                       |
| [PAPERLESS_ADMIN_USER](#paperless_admin_user)           | `string`  | Optional | cannot be null | [configure-module](configure-module-validate-input-properties-paperless_admin_user.md "https://schema.nethserver.org/paperlessngx/configure-module-validate-input.json#/properties/PAPERLESS_ADMIN_USER")           |
| [PAPERLESS_ADMIN_PASSWORD](#paperless_admin_password)   | `string`  | Optional | cannot be null | [configure-module](configure-module-validate-input-properties-paperless_admin_password.md "https://schema.nethserver.org/paperlessngx/configure-module-validate-input.json#/properties/PAPERLESS_ADMIN_PASSWORD")   |
| [PAPERLESS_ADMIN_MAIL](#paperless_admin_mail)           | `string`  | Optional | cannot be null | [configure-module](configure-module-validate-input-properties-paperless_admin_mail.md "https://schema.nethserver.org/paperlessngx/configure-module-validate-input.json#/properties/PAPERLESS_ADMIN_MAIL")           |
| [PAPERLESS_TIME_ZONE](#paperless_time_zone)             | `string`  | Optional | cannot be null | [configure-module](configure-module-validate-input-properties-paperless_time_zone.md "https://schema.nethserver.org/paperlessngx/configure-module-validate-input.json#/properties/PAPERLESS_TIME_ZONE")             |
| [PAPERLESS_OCR_LANGUAGE](#paperless_ocr_language)       | `string`  | Optional | cannot be null | [configure-module](configure-module-validate-input-properties-paperless_ocr_language.md "https://schema.nethserver.org/paperlessngx/configure-module-validate-input.json#/properties/PAPERLESS_OCR_LANGUAGE")       |
| [PAPERLESS_COOKIE_PREFIX](#paperless_cookie_prefix)     | `string`  | Optional | cannot be null | [configure-module](configure-module-validate-input-properties-paperless_cookie_prefix.md "https://schema.nethserver.org/paperlessngx/configure-module-validate-input.json#/properties/PAPERLESS_COOKIE_PREFIX")     |
| [host](#host)                                           | `string`  | Required | cannot be null | [configure-module](configure-module-validate-input-properties-host.md "https://schema.nethserver.org/paperlessngx/configure-module-validate-input.json#/properties/host")                                           |
| [PAPERLESS_URL](#paperless_url)                         | `string`  | Optional | cannot be null | [configure-module](configure-module-validate-input-properties-paperless_url.md "https://schema.nethserver.org/paperlessngx/configure-module-validate-input.json#/properties/PAPERLESS_URL")                         |
| [POSTGRES_DB](#postgres_db)                             | `string`  | Optional | cannot be null | [configure-module](configure-module-validate-input-properties-postgres_db.md "https://schema.nethserver.org/paperlessngx/configure-module-validate-input.json#/properties/POSTGRES_DB")                             |
| [POSTGRES_USER](#postgres_user)                         | `string`  | Optional | cannot be null | [configure-module](configure-module-validate-input-properties-postgres_user.md "https://schema.nethserver.org/paperlessngx/configure-module-validate-input.json#/properties/POSTGRES_USER")                         |
| [POSTGRES_PASSWORD](#postgres_password)                 | `string`  | Optional | cannot be null | [configure-module](configure-module-validate-input-properties-postgres_password.md "https://schema.nethserver.org/paperlessngx/configure-module-validate-input.json#/properties/POSTGRES_PASSWORD")                 |
| [PAPERLESS_TIKA_ENABLED](#paperless_tika_enabled)       | `boolean` | Optional | cannot be null | [configure-module](configure-module-validate-input-properties-paperless_tika_enabled.md "https://schema.nethserver.org/paperlessngx/configure-module-validate-input.json#/properties/PAPERLESS_TIKA_ENABLED")       |
| [PHP_ENABLE_OPCACHE](#php_enable_opcache)               | `boolean` | Optional | cannot be null | [configure-module](configure-module-validate-input-properties-php_enable_opcache.md "https://schema.nethserver.org/paperlessngx/configure-module-validate-input.json#/properties/PHP_ENABLE_OPCACHE")               |
| [PHP_MEMORY_LIMIT](#php_memory_limit)                   | `string`  | Optional | cannot be null | [configure-module](configure-module-validate-input-properties-php_memory_limit.md "https://schema.nethserver.org/paperlessngx/configure-module-validate-input.json#/properties/PHP_MEMORY_LIMIT")                   |
| [PAPERLESS_FILENAME_FORMAT](#paperless_filename_format) | `string`  | Optional | cannot be null | [configure-module](configure-module-validate-input-properties-paperless_filename_format.md "https://schema.nethserver.org/paperlessngx/configure-module-validate-input.json#/properties/PAPERLESS_FILENAME_FORMAT") |
| [http2https](#http2https)                               | `boolean` | Optional | cannot be null | [configure-module](configure-module-validate-input-properties-http2https.md "https://schema.nethserver.org/paperlessngx/configure-module-validate-input.json#/properties/http2https")                               |
| [lets_encrypt](#lets_encrypt)                           | `boolean` | Optional | cannot be null | [configure-module](configure-module-validate-input-properties-lets_encrypt.md "https://schema.nethserver.org/paperlessngx/configure-module-validate-input.json#/properties/lets_encrypt")                           |

## paperless_name



`paperless_name`

* is optional

* Type: `string`

* cannot be null

* defined in: [configure-module](configure-module-validate-input-properties-paperless_name.md "https://schema.nethserver.org/paperlessngx/configure-module-validate-input.json#/properties/paperless_name")

### paperless_name Type

`string`

### paperless_name Constraints

**pattern**: the string must match the following regular expression:&#x20;

```regexp
^[^\r\n]*$
```

[try pattern](https://regexr.com/?expression=%5E%5B%5E%5Cr%5Cn%5D*%24 "try regular expression with regexr.com")

## PAPERLESS_ADMIN_USER



`PAPERLESS_ADMIN_USER`

* is optional

* Type: `string`

* cannot be null

* defined in: [configure-module](configure-module-validate-input-properties-paperless_admin_user.md "https://schema.nethserver.org/paperlessngx/configure-module-validate-input.json#/properties/PAPERLESS_ADMIN_USER")

### PAPERLESS_ADMIN_USER Type

`string`

### PAPERLESS_ADMIN_USER Constraints

**pattern**: the string must match the following regular expression:&#x20;

```regexp
^[^\r\n]*$
```

[try pattern](https://regexr.com/?expression=%5E%5B%5E%5Cr%5Cn%5D*%24 "try regular expression with regexr.com")

## PAPERLESS_ADMIN_PASSWORD



`PAPERLESS_ADMIN_PASSWORD`

* is optional

* Type: `string`

* cannot be null

* defined in: [configure-module](configure-module-validate-input-properties-paperless_admin_password.md "https://schema.nethserver.org/paperlessngx/configure-module-validate-input.json#/properties/PAPERLESS_ADMIN_PASSWORD")

### PAPERLESS_ADMIN_PASSWORD Type

`string`

### PAPERLESS_ADMIN_PASSWORD Constraints

**pattern**: the string must match the following regular expression:&#x20;

```regexp
^[^\r\n]*$
```

[try pattern](https://regexr.com/?expression=%5E%5B%5E%5Cr%5Cn%5D*%24 "try regular expression with regexr.com")

## PAPERLESS_ADMIN_MAIL



`PAPERLESS_ADMIN_MAIL`

* is optional

* Type: `string`

* cannot be null

* defined in: [configure-module](configure-module-validate-input-properties-paperless_admin_mail.md "https://schema.nethserver.org/paperlessngx/configure-module-validate-input.json#/properties/PAPERLESS_ADMIN_MAIL")

### PAPERLESS_ADMIN_MAIL Type

`string`

### PAPERLESS_ADMIN_MAIL Constraints

**pattern**: the string must match the following regular expression:&#x20;

```regexp
^[^\r\n]*$
```

[try pattern](https://regexr.com/?expression=%5E%5B%5E%5Cr%5Cn%5D*%24 "try regular expression with regexr.com")

## PAPERLESS_TIME_ZONE



`PAPERLESS_TIME_ZONE`

* is optional

* Type: `string`

* cannot be null

* defined in: [configure-module](configure-module-validate-input-properties-paperless_time_zone.md "https://schema.nethserver.org/paperlessngx/configure-module-validate-input.json#/properties/PAPERLESS_TIME_ZONE")

### PAPERLESS_TIME_ZONE Type

`string`

### PAPERLESS_TIME_ZONE Constraints

**pattern**: the string must match the following regular expression:&#x20;

```regexp
^[^\r\n]*$
```

[try pattern](https://regexr.com/?expression=%5E%5B%5E%5Cr%5Cn%5D*%24 "try regular expression with regexr.com")

## PAPERLESS_OCR_LANGUAGE



`PAPERLESS_OCR_LANGUAGE`

* is optional

* Type: `string`

* cannot be null

* defined in: [configure-module](configure-module-validate-input-properties-paperless_ocr_language.md "https://schema.nethserver.org/paperlessngx/configure-module-validate-input.json#/properties/PAPERLESS_OCR_LANGUAGE")

### PAPERLESS_OCR_LANGUAGE Type

`string`

### PAPERLESS_OCR_LANGUAGE Constraints

**pattern**: the string must match the following regular expression:&#x20;

```regexp
^[^\r\n]*$
```

[try pattern](https://regexr.com/?expression=%5E%5B%5E%5Cr%5Cn%5D*%24 "try regular expression with regexr.com")

## PAPERLESS_COOKIE_PREFIX



`PAPERLESS_COOKIE_PREFIX`

* is optional

* Type: `string`

* cannot be null

* defined in: [configure-module](configure-module-validate-input-properties-paperless_cookie_prefix.md "https://schema.nethserver.org/paperlessngx/configure-module-validate-input.json#/properties/PAPERLESS_COOKIE_PREFIX")

### PAPERLESS_COOKIE_PREFIX Type

`string`

### PAPERLESS_COOKIE_PREFIX Constraints

**pattern**: the string must match the following regular expression:&#x20;

```regexp
^[^\r\n]*$
```

[try pattern](https://regexr.com/?expression=%5E%5B%5E%5Cr%5Cn%5D*%24 "try regular expression with regexr.com")

## host



`host`

* is required

* Type: `string`

* cannot be null

* defined in: [configure-module](configure-module-validate-input-properties-host.md "https://schema.nethserver.org/paperlessngx/configure-module-validate-input.json#/properties/host")

### host Type

`string`

### host Constraints

**minimum length**: the minimum number of characters for this string is: `1`

**pattern**: the string must match the following regular expression:&#x20;

```regexp
^[^\r\n]*$
```

[try pattern](https://regexr.com/?expression=%5E%5B%5E%5Cr%5Cn%5D*%24 "try regular expression with regexr.com")

## PAPERLESS_URL

Deprecated compatibility field; ignored by configure-module.

`PAPERLESS_URL`

* is optional

* Type: `string`

* cannot be null

* defined in: [configure-module](configure-module-validate-input-properties-paperless_url.md "https://schema.nethserver.org/paperlessngx/configure-module-validate-input.json#/properties/PAPERLESS_URL")

### PAPERLESS_URL Type

`string`

### PAPERLESS_URL Constraints

**pattern**: the string must match the following regular expression:&#x20;

```regexp
^[^\r\n]*$
```

[try pattern](https://regexr.com/?expression=%5E%5B%5E%5Cr%5Cn%5D*%24 "try regular expression with regexr.com")

## POSTGRES_DB

Deprecated compatibility field; ignored by configure-module.

`POSTGRES_DB`

* is optional

* Type: `string`

* cannot be null

* defined in: [configure-module](configure-module-validate-input-properties-postgres_db.md "https://schema.nethserver.org/paperlessngx/configure-module-validate-input.json#/properties/POSTGRES_DB")

### POSTGRES_DB Type

`string`

### POSTGRES_DB Constraints

**pattern**: the string must match the following regular expression:&#x20;

```regexp
^[^\r\n]*$
```

[try pattern](https://regexr.com/?expression=%5E%5B%5E%5Cr%5Cn%5D*%24 "try regular expression with regexr.com")

## POSTGRES_USER

Deprecated compatibility field; ignored by configure-module.

`POSTGRES_USER`

* is optional

* Type: `string`

* cannot be null

* defined in: [configure-module](configure-module-validate-input-properties-postgres_user.md "https://schema.nethserver.org/paperlessngx/configure-module-validate-input.json#/properties/POSTGRES_USER")

### POSTGRES_USER Type

`string`

### POSTGRES_USER Constraints

**pattern**: the string must match the following regular expression:&#x20;

```regexp
^[^\r\n]*$
```

[try pattern](https://regexr.com/?expression=%5E%5B%5E%5Cr%5Cn%5D*%24 "try regular expression with regexr.com")

## POSTGRES_PASSWORD

Deprecated compatibility field; ignored by configure-module.

`POSTGRES_PASSWORD`

* is optional

* Type: `string`

* cannot be null

* defined in: [configure-module](configure-module-validate-input-properties-postgres_password.md "https://schema.nethserver.org/paperlessngx/configure-module-validate-input.json#/properties/POSTGRES_PASSWORD")

### POSTGRES_PASSWORD Type

`string`

### POSTGRES_PASSWORD Constraints

**pattern**: the string must match the following regular expression:&#x20;

```regexp
^[^\r\n]*$
```

[try pattern](https://regexr.com/?expression=%5E%5B%5E%5Cr%5Cn%5D*%24 "try regular expression with regexr.com")

## PAPERLESS_TIKA_ENABLED

Deprecated compatibility field; ignored by configure-module.

`PAPERLESS_TIKA_ENABLED`

* is optional

* Type: `boolean`

* cannot be null

* defined in: [configure-module](configure-module-validate-input-properties-paperless_tika_enabled.md "https://schema.nethserver.org/paperlessngx/configure-module-validate-input.json#/properties/PAPERLESS_TIKA_ENABLED")

### PAPERLESS_TIKA_ENABLED Type

`boolean`

## PHP_ENABLE_OPCACHE

Deprecated compatibility field; ignored by configure-module.

`PHP_ENABLE_OPCACHE`

* is optional

* Type: `boolean`

* cannot be null

* defined in: [configure-module](configure-module-validate-input-properties-php_enable_opcache.md "https://schema.nethserver.org/paperlessngx/configure-module-validate-input.json#/properties/PHP_ENABLE_OPCACHE")

### PHP_ENABLE_OPCACHE Type

`boolean`

## PHP_MEMORY_LIMIT

Deprecated compatibility field; ignored by configure-module.

`PHP_MEMORY_LIMIT`

* is optional

* Type: `string`

* cannot be null

* defined in: [configure-module](configure-module-validate-input-properties-php_memory_limit.md "https://schema.nethserver.org/paperlessngx/configure-module-validate-input.json#/properties/PHP_MEMORY_LIMIT")

### PHP_MEMORY_LIMIT Type

`string`

### PHP_MEMORY_LIMIT Constraints

**pattern**: the string must match the following regular expression:&#x20;

```regexp
^[^\r\n]*$
```

[try pattern](https://regexr.com/?expression=%5E%5B%5E%5Cr%5Cn%5D*%24 "try regular expression with regexr.com")

## PAPERLESS_FILENAME_FORMAT



`PAPERLESS_FILENAME_FORMAT`

* is optional

* Type: `string`

* cannot be null

* defined in: [configure-module](configure-module-validate-input-properties-paperless_filename_format.md "https://schema.nethserver.org/paperlessngx/configure-module-validate-input.json#/properties/PAPERLESS_FILENAME_FORMAT")

### PAPERLESS_FILENAME_FORMAT Type

`string`

### PAPERLESS_FILENAME_FORMAT Constraints

**pattern**: the string must match the following regular expression:&#x20;

```regexp
^[^\r\n]*$
```

[try pattern](https://regexr.com/?expression=%5E%5B%5E%5Cr%5Cn%5D*%24 "try regular expression with regexr.com")

## http2https



`http2https`

* is optional

* Type: `boolean`

* cannot be null

* defined in: [configure-module](configure-module-validate-input-properties-http2https.md "https://schema.nethserver.org/paperlessngx/configure-module-validate-input.json#/properties/http2https")

### http2https Type

`boolean`

## lets_encrypt



`lets_encrypt`

* is optional

* Type: `boolean`

* cannot be null

* defined in: [configure-module](configure-module-validate-input-properties-lets_encrypt.md "https://schema.nethserver.org/paperlessngx/configure-module-validate-input.json#/properties/lets_encrypt")

### lets_encrypt Type

`boolean`
