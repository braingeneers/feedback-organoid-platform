from scipy.optimize import curve_fit

class CurveFitting:

    @staticmethod
    def parabola(x, a, b, c):
        return a * x**2 + b * x + c

    @staticmethod
    def polinomial_3(x, a, b, c, d):
        return a * x**3 + b * x**2 + c*x + d

    @staticmethod
    def polinomial_4(x, a, b, c, d, e):
        return a * x**4 + b * x**3 + c*x**2 + d*x + e

    @staticmethod
    def polinomial_5(x, a, b, c, d, e, f):
        return a * x**5 + b * x**4 + c*x**3 + d*x**2 + e*x + f

    @staticmethod
    def polinomial_6(x, a, b, c, d, e, f, g):
        return a * x**6 + b * x**5 + c*x**4 + d*x**3 + e*x**2 + f*x + g

    CURVE_FUNCTIONS = {
        'parabola': parabola,
        'polinomial_3': polinomial_3,
        'polinomial_4': polinomial_4,
        'polinomial_5': polinomial_5,
        'polinomial_6': polinomial_6
    }
    @staticmethod
    def fit_curve(curve_type, x_data, y_data):
        if curve_type in CurveFitting.CURVE_FUNCTIONS:
            curve_func = CurveFitting.CURVE_FUNCTIONS[curve_type].__func__  # Access the underlying function
            params, _ = curve_fit(curve_func, x_data, y_data)
            return curve_func, params
        else:
            raise ValueError(f"Invalid curve type: {curve_type}")