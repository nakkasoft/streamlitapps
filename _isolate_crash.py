"""pyarrow segfault 최소 재현: pandas -> pyarrow 변환 자체가 문제인지 확인."""

import pandas as pd

print("step 1: creating dataframe")
df = pd.DataFrame({
    "a": ["x", "y", "z"] * 10,
    "b": [1, 2, 3] * 10,
})
print("step 2: dataframe created, rows=", len(df))

print("step 3: importing pyarrow")
import pyarrow as pa
print("step 3 done, pyarrow version:", pa.__version__)

print("step 4: converting to arrow table")
table = pa.Table.from_pandas(df)
print("step 4 done, table rows:", table.num_rows)

print("step 5: streamlit dataframe serializer")
from streamlit.dataframe_util import convert_anything_to_pandas_df
print("step 5 import OK")

print("ALL STEPS COMPLETED WITHOUT CRASH")
