# bohe-api-auto-sign

![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)
![License](https://img.shields.io/badge/license-Modified_MIT-red.svg)

> Automation solution for Bohe Public Welfare Station (up.x666.me) daily sign-in and lucky draw.

---

> [!IMPORTANT]
> In addition to the standard MIT license, you must also comply with the following: This project is strictly prohibited from being used for any form of commercial behavior. It is strictly forbidden to integrate it into paid platforms or paid automated services.

---

## Credential Acquisition

This project involves three core credentials. You can provide only `linux_do_token` and let the program handle the automation, or manually fill in other tokens to bypass the login flow.
We recommend logging in and obtaining tokens in an InPrivate/Incognito window. Tokens refresh with browsing status, so please let the program manage the token lifecycle.

### 1. `linux_do_token`
*   **Source**: Session persistence cookie from the `linux.do` site.
*   **How to get**: After logging in to `linux.do`, find the value of `_t` in Developer Tools (F12) -> Application -> Cookies. This is the recommended method and has the longest validity.

### 2. `linux_do_connect_token`
*   **Source**: Connection credential from the `connect.linux.do` authorization center.
*   **How to get**: After logging in to `linux.do`, find the value of `auth.session-token` in Developer Tools (F12) -> Application -> Cookies.
*   **Note**: Providing only this token will work. However, we still recommend using `linux_do_token` directly, as it can renew all tokens.

### 3. `bohe_sign_token`
*   **Source**: Backend JWT from `up.x666.me`.
*   **How to get**: After logging in on the Bohe sign-in page, find the value of `userToken` in Developer Tools (F12) -> Application -> Local storage.
*   **Note**: Providing only this token will work. However, we still recommend using `linux_do_token` directly, as it can renew all tokens.
