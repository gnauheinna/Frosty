from snowflake.cortex import Complete, ExtractAnswer, Sentiment, Summarize, Translate

text = """

    The Snowflake company was co-founded by Thierry Cruanes, Marcin Zukowski,

    and Benoit Dageville in 2012 and is headquartered in Bozeman, Montana.

"""


print(Complete("llama2-70b-chat", "how do snowflakes get their unique patterns?"))
print(ExtractAnswer(text, "When was snowflake founded?"))
print(Sentiment("I really enjoyed this restaurant. Fantastic service!"))
print(Summarize(text))
print(Translate(text, "en", "fr"))