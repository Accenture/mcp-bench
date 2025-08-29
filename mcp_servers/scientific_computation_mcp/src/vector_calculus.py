import numpy as np
import sympy as sp
from sympy.parsing.sympy_parser import standard_transformations, implicit_multiplication_application
from sympy import parse_expr
from sympy.vector import Del, CoordSys3D, directional_derivative

C = CoordSys3D('C')


def parse_field(f_str: str):
    """
    Parse a vector field string into a Sympy Vector.

    Args:
        f_str (str): e.g. "[z, -y, x]".
        x_coord, y_coord, z_coord: optional sympy symbols (e.g., x, C.x).
          If None, defaults to bare symbols (x, y, z).

    Returns:
        sympy.vector.Vector: symbolic vector in CoordSys3D C.
    """

    raw = f_str.strip().strip("[]")
    comps_str = [c.strip() for c in raw.split(",")]

    transformations = standard_transformations + (implicit_multiplication_application,)
    local_ns = {
        "x": C.x, "y": C.y, "z": C.z,
        "sin": sp.sin, "cos": sp.cos
    }

    comp_syms = [
        parse_expr(expr, local_dict=local_ns, transformations=transformations)
        for expr in comps_str
    ]

    return comp_syms[0] * C.i + comp_syms[1] * C.j + comp_syms[2] * C.k


def register_tools(mcp, tensor_store):
    # Basic vector operations

    @mcp.tool()
    def vector_project(name: str, new_vector: list[float]) -> np.ndarray:
        """
        Projects a stored vector onto another vector.

        Args:
            name (str): Name of the stored vector to project.
            new_vector (list[float]): The vector to project onto.

        Returns:
            np.ndarray: The projection result vector.

        Raises:
            ValueError: If the vector name is not found or projection fails.
        """
        if name not in tensor_store:
            raise ValueError("The tensor name is not found in the store.")

        try:
            new_vector = np.asarray(new_vector)
            result = np.dot(tensor_store[name], new_vector) / np.linalg.norm(new_vector) * new_vector
        except ValueError as e:
            raise ValueError(f"Error computing projection:{e}")

        return result

    @mcp.tool()
    def vector_dot_product(name_a: str, name_b: str) -> np.ndarray:
        """
        Computes the dot product between two stored vectors.

        Args:
            name_a (str): Name of the first vector in the tensor store.
            name_b (str): Name of the second vector in the tensor store.

        Returns:
            np.ndarray: Scalar result of the dot product.

        Raises:
            ValueError: If either vector is not found or if the dot product computation fails.
        """
        if name_a not in tensor_store or name_b not in tensor_store:
            raise ValueError("One or both tensor names not found in the store.")

        try:
            result = np.dot(tensor_store[name_a], tensor_store[name_b])
        except ValueError as e:
            raise ValueError(f"Error computing dot product:{e}")

        return result

    @mcp.tool()
    def vector_cross_product(name_a: str, name_b: str) -> np.ndarray:
        """
        Computes the cross product of two stored vectors.

        Args:
            name_a (str): Name of the first vector in the tensor store.
            name_b (str): Name of the second vector in the tensor store.

        Returns:
            np.ndarray: Vector result of the cross product.

        Raises:
            ValueError: If either vector is not found or if the cross product computation fails.
        """
        if name_a not in tensor_store or name_b not in tensor_store:
            raise ValueError("One or both tensor names not found in the store.")

        try:
            result = np.cross(tensor_store[name_a], tensor_store[name_b])
        except ValueError as e:
            raise ValueError(f"Error computing cross product:{e}")

        return result

    @mcp.tool()
    def gradient(f_str: str) -> str:
        """
        Computes the symbolic gradient of a scalar function.

        Args:
            f_str (str): A string representing a scalar function (e.g., "x**2 + y*z").

        Returns:
            str: A string representation of the symbolic gradient as a vector.
        """
        f_sym = sp.sympify(f_str)
        variable = sorted(list(f_sym.free_symbols), key=lambda s: s.name)
        grad = sp.Matrix([f_sym]).jacobian(variable)
        return grad

    @mcp.tool()
    def curl(f_str: str, point: list[float] = None) -> dict:
        """
        Computes the symbolic curl of a vector field, optionally evaluated at a point.

        Args:
            f_str (str): A string representing the vector field in list format (e.g., "[x+y, x, 2*z]").
            point (list[float], optional): A list of coordinates [x, y, z] to evaluate the curl numerically.

        Returns:
            dict: A dictionary with the symbolic curl as a string, and optionally the evaluated vector.
        """

        F = parse_field(f_str)

        curl_sym = Del().cross(F).doit()

        result = {"curl_sym": str(curl_sym)}

        if point:
            variables = [C.x, C.y, C.z]
            comps = [curl_sym.dot(dir_) for dir_ in (C.i, C.j, C.k)]
            lamb = sp.lambdify(variables, sp.Matrix(comps), 'numpy')
            result['curl_val'] = [float(v) for v in lamb(*point)]
        return result

    @mcp.tool()
    def divergence(f_str: str, point: list[float] = None) -> dict:
        """
        Computes the symbolic divergence of a vector field, optionally evaluated at a point.

        Args:
            f_str (str): A string representing the vector field in list format (e.g., "[x+y, x, 2*z]").
            point (list[float], optional): A list of coordinates [x, y, z] to evaluate the divergence numerically.

        Returns:
            dict: A dictionary with the symbolic divergence as a string, and optionally the evaluated scalar.
        """

        F = parse_field(f_str)

        div_sym = Del().dot(F, doit=True)
        result = {'divergence_sym': str(div_sym)}

        if point:
            variables = [C.x, C.y, C.z]
            lamb = sp.lambdify(variables, div_sym, 'numpy')
            result['divergence_val'] = float(lamb(*point))
        return result

    @mcp.tool()
    def laplacian(f_str: str, is_vector: bool = False) -> str:
        """
        Computes the Laplacian of a scalar or vector field symbolically.

        Args:
            f_str (str): Scalar function as "x**2 + y*z" or vector "[Fx, Fy, Fz]".
            is_vector (bool): Set True to compute vector Laplacian.

        Returns:
            str: Symbolic result of the Laplacian—scalar or list of 3 components.
        """
        if not is_vector:
            f = parse_expr(f_str, local_dict={"x": C.x, "y": C.y, "z": C.z})
            lap = Del().dot(Del()(f)).doit()
            return str(lap)
        else:
            F = parse_field(f_str)
            # Extract components
            comps = F.to_matrix(C).tolist()
            lap_comps = [Del().dot(Del()(comp)).doit() for comp in comps]
            return str(lap_comps)  # list form

    @mcp.tool()
    def directional_deriv(f_str: str, u: list[float], unit: bool = True) -> str:
        """
        Computes symbolic directional derivative of scalar field along a vector direction.

        Args: f_str (str): Expression like "x*y*z". u (list[float]): Direction vector [vx, vy, vz]. unit (bool): True
        if u should be normalized before calculating directional derivative. Set to True by default.

        Returns:
            str: Symbolic result as string.
        """
        f = parse_expr(f_str, local_dict={"x": C.x, "y": C.y, "z": C.z})
        v = u[0] * C.i + u[1] * C.j + u[2] * C.k

        if unit:
            v = v.normalize()

        expr = directional_derivative(f, v).doit()
        return str(expr)