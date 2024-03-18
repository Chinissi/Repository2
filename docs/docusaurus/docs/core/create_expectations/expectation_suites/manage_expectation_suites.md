---
sidebar_label: 'Manage Expectation Suites'
title: 'Manage Expectation Suites'
description: Create and manage GX Core Expectation Suites with Python.
---

An Expectation Suite contains a group of Expectations that describe the same set of data.  All the Expectations that you apply to your data are grouped into an Expectation Suite.

## Prerequisites

- Installed Python.
- Installed the GX Core library.

## Create an Expectation Suite

1. Import the GX Core library and the `ExpectationSuite` class:

  ```python title="Python code" name="core/expectation_suites/_examples/create_an_expectation_suite.py imports"
  ```

2. Get a Data Context:

  ```python title="Python code" name="core/expectation_suites/_examples/create_an_expectation_suite.py get_context"
  ```

3. Create an Expectation Suite:

  ```python title="Python code" name="core/expectation_suites/_examples/create_an_expectation_suite.py create Expectation Suite"
  ```

4. Add the Expectation Suite to your Data Context:

  ```python title="Python code" name="core/expectation_suites/_examples/create_an_expectation_suite.py add snippet to Data Context"
  ```

:::tip

You can add an Expectation Suite to your Data Context at the same time as you create the Expectation Suite with the following code:

```python title="Python code" name="core/expectation_suites/_examples/create_an_expectation_suite.py create and add Expectation Suite to Data Context"
```

:::

<details>
<summary>Full example code</summary>
<p>

```python title="Python code" name="core/expectation_suites/_examples/create_an_expectation_suite.py full example code"
```

</p>
</details>

## Get an existing Expectation Suite

1. Import the GX Core library:

  ```python title="Python code" name="core/expectation_suites/_examples/get_an_expectation_suite.py imports"
  ```

2. Get a Data Context:

  ```python title="Python code" name="core/expectation_suites/_examples/get_an_expectation_suite.py get_context"
  ```

3. Use the Data Context to retrieve the existing Expectation Suite:

  ```python title="Python code" name="core/expectation_suites/_examples/get_an_expectation_suite.py create Expectation Suite"
  ```

<details>
<summary>Full example code</summary>
<p>

```python title="Python code" name="core/expectation_suites/_examples/get_an_expectation_suite.py full example code"
```

</p>
</details>

## Delete an Expectation Suite

1. Import the GX Core library:

  ```python title="Python code" name="core/expectation_suites/_examples/delete_an_expectation_suite.py imports"
  ```

2. Get a Data Context:

  ```python title="Python code" name="core/expectation_suites/_examples/delete_an_expectation_suite.py get_context"
  ```

3. Get the Expectation Suite to delete from the Data Context:

  ```python title="Python code" name="core/expectation_suites/_examples/delete_an_expectation_suite.py get Expectation Suite"
  ```

4. Use the Data Context to delete an existing Expectation Suite:

  ```python title="Python code" name="core/expectation_suites/_examples/delete_an_expectation_suite.py delete Expectation Suite"
  ```

<details>
<summary>Full example code</summary>
<p>

```python title="Python code" name="core/expectation_suites/_examples/delete_an_expectation_suite.py full example code"
```

</p>
</details>

## Add Expectations to an Expectation Suite

1. Import the GX Core library and `expectations` module:

  ```python title="Python code" name="core/expectation_suites/_examples/add_expectations_to_an_expectation_suite.py imports"
  ```

2. Get a Data Context:

  ```python title="Python code" name="core/expectation_suites/_examples/add_expectations_to_an_expectation_suite.py get_context"
  ```

3. [Create a new](#create-a-new-expectation-suite) or [get an existing](#get-an-existing-expectation-suite) Expectation Suite.  This example retrieves an existing Expectation Suite:

  ```python title="Python code" name="core/expectation_suites/_examples/add_expectations_to_an_expectation_suite.py get_suite"
  ```

4. Create an Expectation:

  ```python title="Python code" name="core/expectation_suites/_examples/add_expectations_to_an_expectation_suite.py create an Expectation"
  ```

  The specific parameters you provide when initializing an Expectation are determined by the Expectation class.  You can view available Expectations and the parameters they take in the [Expectation Gallery](https://greatexpectations.io/expectations).

5. Add the Expectation to the Expectation Suite:

  ```python title="Python code" name="core/expectation_suites/_examples/add_expectations_to_an_expectation_suite.py add an Expectation to an Expectation Suite"
  ```

  :::tip 
  
  You can create an Expectation at the same time as you add it to the Expectation Suite:

  ```python title="Python code" name="core/expectation_suites/_examples/add_expectations_to_an_expectation_suite.py create and add an Expectation"
  ```
  
  :::

<details>
<summary>Full example code</summary>
<p>

```python title="Python code" name="core/expectation_suites/_examples/add_expectations_to_an_expectation_suite.py full example code"
```

</p>
</details>

## Get an Expectation from an Expectation Suite

1. Import the GX Core library and `expectations` module:

  ```python title="Python code" name="core/expectation_suites/_examples/get_a_specific_expectation_from_an_expectation_suite.py imports"
  ```

2. Get a Data Context:

  ```python title="Python code" name="core/expectation_suites/_examples/get_a_specific_expectation_from_an_expectation_suite.py get_context"
  ```

3. [Get an existing Expectation Suite](#get-an-existing-expectation-suite) that contains Expectations, or [create a new Expectation Suite](#create-a-new-expectation-suite) and [add some Expectations to it](#add-expectations-to-an-expectation-suite).  This example retrieves an existing Expectation Suite:

  ```python title="Python code" name="core/expectation_suites/_examples/get_a_specific_expectation_from_an_expectation_suite.py retrieve Expectation Suite"
  ```

4. Find the desired Expectation by iterating the Expectation Suite's Expectations and comparing classes and attributes to those of the desired Expectation:

  ```python title="Python code" name="core/expectation_suites/_examples/get_a_specific_expectation_from_an_expectation_suite.py retrieve expectation"
  ```

<details>
<summary>Full example code</summary>
<p>

```python title="Python code" name="core/expectation_suites/_examples/get_a_specific_expectation_from_an_expectation_suite.py full example code"
```

</p>
</details>

## Edit a single Expectation in an Expectation Suite

1. Import the GX Core library and the `expectations` module:

  ```python title="Python code" name="core/expectation_suites/_examples/get_a_specific_expectation_from_an_expectation_suite.py imports"
  ```

2. Get a Data Context:

  ```python title="Python code" name="core/expectation_suites/_examples/edit_a_single_expectation.py get data context"
  ```

3. [Get the Expectation to edit](#get-a-specific-expectation-from-an-expectation-suite) from its Expectation Suite:

  ```python title="Python code" name="core/expectation_suites/_examples/edit_a_single_expectation.py get expectation to edit"
  ```

5. [Modify the Expectation](/core/create_expectations/expectations/manage_expectations.md#modify-an-expectation-in-an-expecatation-suite):

  ```python title="Python code" name="core/expectation_suites/_examples/edit_a_single_expectation.py edit attribute"
  ```

6. Save the modified Expectation in the Expectation Suite:

  ```python title="Python code" name="core/expectation_suites/_examples/edit_a_single_expectation.py save the Expectation"
  ```

  :::info
  `expectation.save()` is explicitly used to update the configuration of an Expectation in an Expectation Suite.  If the Expectation is not part of an Expectation Suite, `expectation.save()` will fail.
  
  You can [test changes to an Expectation](/core/create_expectations/expectations/manage_expectations.md#test-an-expectation) without running `expectation.save()`, but those changes will not persist in the Expectation Suite until `expectation.save()` is run.
  :::

<details>
<summary>Full example code</summary>
<p>

```python title="Python code" name="core/expectation_suites/_examples/edit_a_single_expectation.py full example code"
```

</p>
</details>

## Edit multiple Expectations in an Expectation Suite

1. [Get an existing Expectation Suite](#get-an-existing-expectation-suite) that contains Expectations, or [create a new Expectation Suite](#create-a-new-expectation-suite) and [add some Expectations to it](#add-expectations-to-an-expectation-suite). 

  This example creates a new Expectation Suite and adds a few Expectations to it:

  ```python title="Python code" name="core/expectation_suites/_examples/edit_all_expectations_in_an_expectation_suite.py create and populate Expectation Suite"
  ```

  If you are editing an existing Expectation Suite, retrieve it with:

  ```python title="Python code" name="core/expectation_suites/_examples/edit_all_expectations_in_an_expectation_suite.py get Expectation Suite"
  ```

2. Modify multiple Expectations in the Expectation Suite:

  ```python title="Python code" name="core/expectation_suites/_examples/edit_all_expectations_in_an_expectation_suite.py modify Expectations"
  ```

3. Save the Expectation Suite and all modifications to the Expectations within it:

  ```python title="Python code" name="core/expectation_suites/_examples/edit_all_expectations_in_an_expectation_suite.py save Expectation Suite"
  ```

<details>
<summary>Full example code</summary>
<p>

```python title="Python code" name="core/expectation_suites/_examples/edit_all_expectations_in_an_expectation_suite.py full example code"
```

</p>
</details>

## Delete an Expectation from an Expectation Suite

1. Import the Great Expectations Library and `expectations` module:

  ```python title="Python code" name="core/expectation_suites/_examples/delete_an_expectation_in_an_expectation_suite.py imports"
  ```

2. Get a Data Context:

  ```python title="Python code" name="core/expectation_suites/_examples/delete_an_expectation_in_an_expectation_suite.py get context"
  ```

3. [Get the Expectation Suite containing the Expectation to delete](#get-an-existing-expectation-suite).  This example retrieves an existing Expectation Suite from the Data Context:

  ```python title="Python code" name="core/expectation_suites/_examples/delete_an_expectation_in_an_expectation_suite.py get Expectation Suite"
  ```

4. [Get the Expectation to delete from its Expectation Suite](#get-a-specific-expectation-from-an-expectation-suite):

  ```python title="Python code" name="core/expectation_suites/_examples/delete_an_expectation_in_an_expectation_suite.py get Expectation"
  ```

5. Use the Expectation Suite to delete the Expectation:

  ```python title="Python code" name="core/expectation_suites/_examples/delete_an_expectation_in_an_expectation_suite.py delete the Expectation"
  ```

<details>
<summary>Full example code</summary>
<p>

```python title="Python code" name="core/expectation_suites/_examples/delete_an_expectation_in_an_expectation_suite.py full example code"
```

</p>
</details>