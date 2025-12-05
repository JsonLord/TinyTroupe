**Computer Use Best Practices**

This document outlines best practices for using the computer_use tool to ensure reliable and accurate results.

**1. Choosing the Right Action**

*   **`navigate`**: Use to open a new URL.
*   **`see`**: Use to confirm that an element is visible on the page before interacting with it. This is crucial for preventing errors caused by elements not being loaded yet.
*   **`click`**: Use to click on buttons, links, and other interactive elements.
*   **`fill`**: Use to enter text into input fields.
*   **`submit`**: Use to submit forms.
*   **`wait`**: Use to pause execution for a specific duration. This can be useful for waiting for animations or other time-based events to complete.
*   **`scroll`**: Use to scroll the page to a specific element or position.
*   **`hover`**: Use to hover over elements to reveal tooltips or other hidden content.
*   **`press_key`**: Use to simulate pressing keyboard keys.

**2. Writing Effective Selectors**

*   Use specific and unique selectors to target elements accurately. IDs are ideal, but you can also use class names, attributes, or a combination of these.
*   Avoid using overly broad selectors that could match multiple elements.
*   Use browser developer tools to inspect elements and find the best selectors.

**3. Handling Dynamic Content**

*   Use the see action to wait for elements to appear before interacting with them.
*   Use the wait action to pause execution and allow time for content to load.
*   Be prepared to handle cases where elements may not be present on the page.

**4. Chaining Actions**

*   Break down complex tasks into a series of smaller, more manageable actions.
*   For example, to fill out and submit a form, you would use a sequence of navigate, fill, and submit actions.

**5. Error Handling**

*   If a `computer_use` call fails, check the logs to identify the cause of the error.
*   Common errors include:
    *   Invalid selectors
    *   Elements not being visible or interactive
    *   Network errors
*   Use the `sequential_thinking` tool to analyze the error and determine the best course of action. This may involve:
    *   Correcting the selector
    *   Adding a wait or see action
    *   Retrying the action

By following these best practices, you can improve the reliability and accuracy of your `computer_use` calls and ensure that your agents can effectively interact with web pages.
