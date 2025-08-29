from io import BytesIO
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from mcp.server.fastmcp import Image
from sympy import symbols
import sympy as sp
from sympy.parsing.sympy_parser import standard_transformations, implicit_multiplication_application, parse_expr, \
    convert_xor
import numpy as np

x, y, z = symbols("x y z")
transforms = standard_transformations + (implicit_multiplication_application, convert_xor)
local_ns = {"x": x, "y": y, "z": z, "sin": sp.sin, "cos": sp.cos}


def register_tools(mcp):
    @mcp.tool()
    def plot_vector_field(f_str: str, bounds=(-1, 1, -1, 1, -1, 1), n: int = 10) -> Image:
        """
        Plots a 3D vector field from a string "[u(x,y,z), v(x,y,z), w(x,y,z)]"

        Args:
            f_str: string representation of 3D field, e.g. "[z, -y, x]".
            bounds: (xmin, xmax, ymin, ymax, zmin, zmax)
            n: grid resolution per axis

        Returns: Displayed Matplotlib 3D quiver plot (no image return needed)
        """
        # 1. Extract component strings
        raw = f_str.strip().lstrip("[").rstrip("]")
        u_s, v_s, w_s = [s.strip() for s in raw.split(",")]

        # 2. Parse each component with bare symbols
        u_expr = parse_expr(u_s, local_dict=local_ns, transformations=transforms)
        v_expr = parse_expr(v_s, local_dict=local_ns, transformations=transforms)
        w_expr = parse_expr(w_s, local_dict=local_ns, transformations=transforms)

        # 3. Convert to numpy functions
        u_fn = sp.lambdify((x, y, z), u_expr, "numpy")
        v_fn = sp.lambdify((x, y, z), v_expr, "numpy")
        w_fn = sp.lambdify((x, y, z), w_expr, "numpy")

        # 4. Prepare grid
        xmin, xmax, ymin, ymax, zmin, zmax = bounds
        X, Y, Z = np.meshgrid(
            np.linspace(xmin, xmax, n),
            np.linspace(ymin, ymax, n),
            np.linspace(zmin, zmax, n),
            indexing="ij"
        )
        U = u_fn(X, Y, Z)
        V = v_fn(X, Y, Z)
        W = w_fn(X, Y, Z)

        try:
            fig = Figure(figsize=(8, 6))
            canvas = FigureCanvas(fig)
            ax = fig.add_subplot(projection="3d")
            ax.quiver(X, Y, Z, U, V, W, length=0.1, normalize=True, color="blue")
            ax.set_xlabel("X")
            ax.set_ylabel("Y")
            ax.set_zlabel("Z")
            ax.set_title(f"3D Vector Field: {f_str}")
            # Save to buffer and return
            buf = BytesIO()
            canvas.print_png(buf)
            img_bytes = buf.getvalue()
        except ValueError as e:
            raise ValueError(f'Error plotting vector field: {e}')

        return Image(data=img_bytes, format="png")

    @mcp.tool()
    def plot_function(expr_str: str, xlim: tuple[int, int] = (-5, 5), ylim: tuple[int, int] = (-5, 5), grid=200) \
            -> Image:

        """
        Plots a 2D or 3D mathematical function from a symbolic expression string.

        Args:
            expr_str: string representation of a function in x or x and y,
                      e.g. "x**2" or "sin(sqrt(x**2 + y**2))"
            xlim: (xmin, xmax) range for x-axis
            ylim: (ymin, ymax) range for y-axis (used in 2D or 3D)
            grid: resolution of the plot grid

        Returns:
            A rendered Image of the function using Matplotlib.
            - 2D plot if the expression contains only x
            - 3D surface plot if the expression contains both x and y
        """
        expr = parse_expr(expr_str, transformations=transforms, local_dict=local_ns)
        vars_used = expr.free_symbols

        # 2. Determine 2D or 3D
        if vars_used == {sp.symbols('x')} or vars_used == set():
            # 2D: f(x)
            f_num = sp.lambdify(x, expr, modules=['numpy'])
            xs = np.linspace(xlim[0], xlim[1], grid)
            ys = f_num(xs)

            fig = Figure()
            ax = fig.add_subplot()
            ax.plot(xs, ys)
            ax.axhline(0, color='black', linewidth=0.8)
            ax.axvline(0, color='black', linewidth=0.8)
            ax.set_xlabel('x')
            ax.set_ylabel(expr_str)
            ax.set_title(f'f(x) = {expr_str}')

        elif vars_used >= {sp.symbols('x'), sp.symbols('y')}:
            # 3D: f(x, y)
            f_num = sp.lambdify((x, y), expr, modules=['numpy'])
            xs = np.linspace(xlim[0], xlim[1], grid)
            ys = np.linspace(ylim[0], ylim[1], grid) if ylim is not None else xs
            X, Y = np.meshgrid(xs, ys)
            Z = f_num(X, Y)

            fig = Figure()
            ax = fig.add_subplot(projection='3d')
            surf = ax.plot_surface(X, Y, Z, cmap='viridis')
            fig.colorbar(surf, ax=ax, shrink=0.6)
            ax.set_title(f'f(x, y) = {expr_str}')
            ax.set_xlabel('x')
            ax.set_ylabel('y')
            ax.set_zlabel(expr_str)

        else:
            raise ValueError("Plot only supports functions in x (2D) or x and y (3D).")

        # 3. Render as PNG
        buf = BytesIO()
        canvas = FigureCanvas(fig)
        canvas.print_png(buf)

        return Image(data=buf.getvalue(), format='png')
