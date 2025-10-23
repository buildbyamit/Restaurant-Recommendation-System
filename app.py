from flask import Flask, render_template, url_for, flash, redirect, request
import pandas as pd

app = Flask(__name__)
lko_rest = pd.read_csv("food1.csv")

def fav(lko_rest1):
    lko_rest1 = lko_rest1.reset_index()
    from sklearn.feature_extraction.text import CountVectorizer
    count1 = CountVectorizer(stop_words='english')
    count_matrix = count1.fit_transform(lko_rest1['highlights'])
    from sklearn.metrics.pairwise import cosine_similarity
    cosine_sim2 = cosine_similarity(count_matrix, count_matrix)
    sim = list(enumerate(cosine_sim2[0]))
    sim = sorted(sim, key=lambda x: x[1], reverse=True)
    sim = sim[1:11]
    indi = [i[0] for i in sim]
    final = lko_rest1.copy().iloc[indi[0]]
    final = pd.DataFrame(final).T
    for i in range(1, len(indi)):
        final1 = pd.DataFrame(lko_rest1.copy().iloc[indi[i]]).T
        final = pd.concat([final, final1])
    return final

def rest_rec(min_cost, cuisine=[], Locality=[], fav_rest="", lko_rest=lko_rest):
    x = min_cost + 500  # Default max budget
    y = min_cost

    # Locality filter (case-insensitive)
    lko_rest1 = lko_rest.copy()[lko_rest['locality'].str.lower().str.strip() == Locality[0].lower().strip()]
    for i in range(1, len(Locality)):
        lko_rest2 = lko_rest.copy()[lko_rest['locality'].str.lower().str.strip() == Locality[i].lower().strip()]
        lko_rest1 = pd.concat([lko_rest1, lko_rest2])
        lko_rest1.drop_duplicates(subset='name', keep='last', inplace=True)

    # Budget filter
    lko_rest_locale = lko_rest1.copy()
    lko_rest_locale = lko_rest_locale[(lko_rest_locale['average_cost_for_one'] <= x) & 
                                      (lko_rest_locale['average_cost_for_one'] >= y)]

    # Cuisine filter (case-insensitive match)
    lko_rest_cui = lko_rest_locale[lko_rest_locale['cuisines'].str.contains(cuisine[0], case=False, na=False)]
    for i in range(1, len(cuisine)):
        lko_rest_cu = lko_rest_locale[lko_rest_locale['cuisines'].str.contains(cuisine[i], case=False, na=False)]
        lko_rest_cui = pd.concat([lko_rest_cui, lko_rest_cu])
        lko_rest_cui.drop_duplicates(subset='name', keep='last', inplace=True)

    if fav_rest != "":
        favr = pd.DataFrame(lko_rest[lko_rest['name'] == fav_rest].drop_duplicates())
        lko_rest3 = pd.concat([favr, lko_rest_cui])
        rest_selected = fav(lko_rest3)
    else:
        lko_rest_cui = lko_rest_cui.sort_values('scope', ascending=False)
        rest_selected = lko_rest_cui.head(10)

    return rest_selected

def calc(min_Price, cuisine, locality):
    # Ignore invalid inputs from dropdown
    if cuisine.lower() == "none" or locality.lower() == "none":
        return []

    rest_sugg = rest_rec(min_Price, [cuisine], [locality])
    if rest_sugg.empty:
        return []

    rest_list1 = rest_sugg.loc[:, ['name', 'address', 'locality', 'timings', 'aggregate_rating', 'url', 'cuisines']]
    rest_list = rest_list1.reset_index(drop=True).T.to_dict()
    res = [value for value in rest_list.values()]
    return res

@app.route("/")
@app.route("/home", methods=['POST'])
def home():
    return render_template('home.html')

@app.route("/search", methods=['POST'])
def search():
    if request.method == 'POST':
        try:
            min_Price = int(request.form['min_Price'])
            cuisine1 = request.form['cuisine']
            locality1 = request.form['locality']
            print(f"🔍 Searching for: ₹{min_Price}, Cuisine: {cuisine1}, Locality: {locality1}")
            res = calc(min_Price, cuisine1, locality1)
            return render_template('search.html', title='Search', restaurants=res)
        except Exception as e:
            print(f"❌ Error: {e}")
            return render_template('search.html', title='Search', restaurants=[])
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
