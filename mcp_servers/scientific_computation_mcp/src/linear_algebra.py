import ast
import numpy as np


def register_tools(mcp, tensor_store):

    # Matrix/tensor operations
    @mcp.tool()
    def add_matrices(name_a: str, name_b: str) -> np.ndarray:
        """
        Adds two stored tensors element-wise.

        Args:
            name_a (str): The name of the first tensor.
            name_b (str): The name of the second tensor.

        Returns:
            np.ndarray: The result of element-wise addition.

        Raises:
            ValueError: If the tensor names are not found or shapes are incompatible.
        """
        if name_a not in tensor_store or name_b not in tensor_store:
            raise ValueError("One or both tensor names not found in the store.")

        try:
            result = np.add(tensor_store[name_a], tensor_store[name_b])
        except ValueError as e:
            raise ValueError(f"Error adding tensors: {e}")

        return result

    @mcp.tool()
    def subtract_matrices(name_a: str, name_b: str) -> np.ndarray:
        """
        Adds two stored tensors element-wise.

        Args:
            name_a (str): The name of the first tensor.
            name_b (str): The name of the second tensor.

        Returns:
            np.ndarray: The result of element-wise subtraction.

        Raises:
            ValueError: If the tensor names are not found or shapes are incompatible.
        """
        if name_a not in tensor_store or name_b not in tensor_store:
            raise ValueError("One or both tensor names not found in the store.")

        try:
            result = np.subtract(tensor_store[name_a], tensor_store[name_b])
        except ValueError as e:
            raise ValueError(f"Error subtracting tensors: {e}")

        return result

    @mcp.tool()
    def multiply_matrices(name_a: str, name_b: str) -> np.ndarray:
        """
        Performs matrix multiplication between two stored tensors.

        Args:
            name_a (str): The name of the first tensor.
            name_b (str): The name of the second tensor.

        Returns:
            np.ndarray: The result of matrix multiplication.

        Raises:
            ValueError: If either tensor is not found or their shapes are incompatible.
        """
        if name_a not in tensor_store or name_b not in tensor_store:
            raise ValueError("One or both tensor names not found in the store.")

        try:
            result = np.matmul(tensor_store[name_a], tensor_store[name_b])
        except ValueError as e:
            raise ValueError(f"Error subtracting tensors: {e}")

        return result

    @mcp.tool()
    def scale_matrix(name: str, scale_factor: float, in_place: bool = True) -> np.ndarray:
        """
        Scales a stored tensor by a scalar factor.

        Args:
            name (str): The name of the tensor to scale.
            scale_factor (float): The scalar value to multiply the tensor by.
            in_place (bool): If True, updates the stored tensor; otherwise, returns a new scaled tensor.

        Returns:
            np.ndarray: The scaled tensor.

        Raises:
            ValueError: If the tensor name is not found in the store.
        """
        if name not in tensor_store:
            raise ValueError("The tensor name is not found in the store.")

        result = tensor_store[name] * scale_factor

        if in_place:
            tensor_store[name] = result

        return result

    @mcp.tool()
    def matrix_inverse(name: str) -> np.ndarray:
        """
        Computes the inverse of a stored square matrix.

        Args:
            name (str): The name of the tensor to invert.

        Returns:
            np.ndarray: The inverse of the matrix.

        Raises:
            ValueError: If the matrix is not found, is not square, or is singular (non-invertible).
        """
        if name not in tensor_store:
            raise ValueError("The tensor name is not found in the store.")

        try:
            result = np.linalg.inv(tensor_store[name])
        except ValueError as e:
            raise ValueError(f"Error computing matrix inverse: {e}")

        return result

    @mcp.tool()
    def transpose(name: str) -> np.ndarray:
        """
        Computes the transpose of a stored tensor.

        Args:
            name (str): The name of the tensor to transpose.

        Returns:
            np.ndarray: The transposed tensor.

        Raises:
            ValueError: If the tensor name is not found in the store.
        """
        if name not in tensor_store:
            raise ValueError("The tensor name is not found in the store.")

        return tensor_store[name].T

    @mcp.tool()
    def determinant(name: str) -> float:
        """
        Computes the determinant of a stored square matrix.

        Args:
            name (str): The name of the matrix.

        Returns:
            float: The determinant of the matrix.

        Raises:
            ValueError: If the matrix is not found or is not square.
        """
        if name not in tensor_store:
            raise ValueError("The tensor name is not found in the store.")

        try:
            result = np.linalg.det(tensor_store[name])
        except ValueError as e:
            raise ValueError(f"Error computing determinant: {e}")

        return result

    @mcp.tool()
    def rank(name: str) -> int | list[int]:
        """
        Computes the rank of a stored tensor.

        Args:
            name (str): The name of the tensor.

        Returns:
            int | list[int]: The rank of the matrix.

        Raises:
            ValueError: If the tensor name is not found in the store.
        """
        if name not in tensor_store:
            raise ValueError("The tensor name is not found in the store.")

        result = np.linalg.matrix_rank(tensor_store[name])
        return result

    @mcp.tool()
    def compute_eigen(name: str) -> dict:
        """
        Computes the eigenvalues and right eigenvectors of a stored square matrix.

        Args:
            name (str): The name of the tensor to analyze.

        Returns:
            dict: A dictionary with keys:
                - 'eigenvalues': np.ndarray
                - 'eigenvectors': np.ndarray

        Raises:
            ValueError: If the tensor is not found or is not a square matrix.
        """
        if name not in tensor_store:
            raise ValueError("The tensor name is not found in the store.")

        try:
            eigenvalues, eigenvectors = np.linalg.eig(tensor_store[name])
        except ValueError as e:
            raise ValueError(f"Error computing eigenvalues and eigenvectors: {e}")

        return {"eigenvalues": eigenvalues, "eigenvectors": eigenvectors}

    # Matrix decompositions
    @mcp.tool()
    def qr_decompose(name: str) -> dict:
        """
        Computes the QR decomposition of a stored matrix.

        Decomposes the matrix A into A = Q @ R, where Q is an orthogonal matrix
        and R is an upper triangular matrix.

        Args:
            name (str): The name of the matrix to decompose.

        Returns:
            dict: A dictionary with keys:
                - 'q': np.ndarray, the orthogonal matrix Q
                - 'r': np.ndarray, the upper triangular matrix R

        Raises:
            ValueError: If the matrix is not found or decomposition fails.
        """
        if name not in tensor_store:
            raise ValueError("The tensor name is not found in the store.")

        try:
            q, r = np.linalg.qr(tensor_store[name])
        except ValueError as e:
            raise ValueError(f"Error computing QR decomposition: {e}")

        return {'q': q, 'r': r}

    @mcp.tool()
    def svd_decompose(name: str) -> dict:
        """
        Computes the Singular Value Decomposition (SVD) of a stored matrix.

        Decomposes the matrix A into A = U @ S @ V^T, where U and V^T are orthogonal
        matrices, and S is a diagonal matrix of singular values.

        Args:
            name (str): The name of the matrix to decompose.

        Returns:
            dict: A dictionary with keys:
                - 'u': np.ndarray, the left singular vectors
                - 's': np.ndarray, the singular values
                - 'v_t': np.ndarray, the right singular vectors transposed

        Raises:
            ValueError: If the matrix is not found or decomposition fails.
        """
        if name not in tensor_store:
            raise ValueError("The tensor name is not found in the store.")

        try:
            u, s, v_t = np.linalg.svd(tensor_store[name])
        except ValueError as e:
            raise ValueError(f"Error computing SVD decomposition: {e}")

        return {'u': u, 's': s, 'v_t': v_t}

    # Bases
    @mcp.tool()
    async def find_orthonormal_basis(name: str) -> list[list[float]]:
        """
        Finds an orthonormal basis for the column space of a stored matrix using QR decomposition.

        Args:
            name (str): The name of the matrix.

        Returns:
            list[list[float]]: A list of orthonormal basis vectors.

        Raises:
            ValueError: If the matrix is not found or decomposition fails.
        """

        try:
            result = await mcp.call_tool("qr_decompose", arguments={'name': name})
            d = ast.literal_eval(result[-1].text)

        except ValueError as e:
            raise ValueError(f"Error computing orthonormal basis: {e}")

        return d['q']

    @mcp.tool()
    def change_basis(name: str, new_basis: list[list[float]]) -> np.ndarray:
        """
        Changes the basis of a stored square matrix.

        Args:
            name (str): Name of the matrix in the tensor store.
            new_basis (list[list[float]]): Columns are new basis vectors.

        Returns:
            np.ndarray: Representation of the matrix in the new basis.

        Raises:
            ValueError: If the matrix name is not found or non-invertible.
        """

        if name not in tensor_store:
            raise ValueError("The tensor name is not found in the store.")

        new_basis = np.asarray(new_basis)
        return np.linalg.inv(new_basis) @ tensor_store[name] @ new_basis
