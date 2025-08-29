from typing import Annotated

import numpy as np
from mcp.server.fastmcp import FastMCP
from pydantic import Field

import linear_algebra
import vector_calculus
import visualization

tensor_store = {}

mcp = FastMCP("scientific_computations")


# Matrix creation, deletion, and modification
@mcp.tool()
def create_tensor(shape: Annotated[list[int], Field(min_items=1, description="Tensor shape as list of integers")],
                  values: Annotated[
                      list[float], Field(min_items=1, description="Flat list of floats to fill the tensor")],
                  name: str) -> np.ndarray:
    """
    Creates a NumPy array (matrix) with a specified shape and values.

    Args:
        shape (list[int]): The shape of the resulting array as a tuple(e.g., (2, 3)).
        values (list[float]): A flat list of values to populate the array.
        name (str): The name of the tensor to be stored.

    Returns:
        np.ndarray: A NumPy array with the specified shape.

    Raises:
        ValueError: If the number of values does not match the product of the shape.
    """

    shape = [int(x) for x in shape]
    values = [float(x) for x in values]

    if len(values) != np.prod(shape):
        raise ValueError("Shape does not match number of values.")
    a = np.array(values).reshape(shape)

    tensor_store[name] = a
    return a


@mcp.tool()
def view_tensor(name: str) -> dict:
    """
    Returns an immutable view of a previously stored NumPy tensor from the in-memory tensor store.

    Args:
        name (str): The name of the tensor as stored in the in-store dictionary
    Returns:
        dict: The in-store dictionary for tensors

    """
    return tensor_store[name]


@mcp.resource("data://tensor_store")
def list_tensor_names() -> str:
    """
    Lists the names of all tensors currently stored in the tensor store.

    Returns:
        str: A newline-separated list of tensor names.
    """
    return "\n".join(tensor_store.keys())


@mcp.tool()
def delete_tensor(name: str):
    """
    Deletes a tensor from the in-memory tensor store.

    Args:
        name (str): The name of the tensor to delete.

    Raises:
        ValueError: If the tensor name is not found in the store or if an error occurs during deletion.
    """

    if name not in tensor_store:
        raise ValueError("One or both tensor names not found in the store.")

    try:
        tensor_store.pop(name)
    except ValueError as e:
        raise ValueError(f"Error removing tensor:{e}")


linear_algebra.register_tools(mcp, tensor_store)
vector_calculus.register_tools(mcp, tensor_store)
visualization.register_tools(mcp)

if __name__ == "__main__":
    mcp.run(transport="stdio")
