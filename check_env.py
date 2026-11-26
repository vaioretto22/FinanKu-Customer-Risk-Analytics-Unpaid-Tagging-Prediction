import sys, importlib
print("Python", sys.version.split()[0])
for m in ["pandas", "numpy", "matplotlib", "seaborn", "sklearn", "scipy",
          "statsmodels", "sqlalchemy", "psycopg2", "joblib", "dotenv"]:
    mod = importlib.import_module(m)
    print(f"OK  {m:<12} {getattr(mod, '__version__', '')}")
