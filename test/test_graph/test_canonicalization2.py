import pytest
import sys

from datetime import datetime
from rdflib import Graph, BNode, Literal, Namespace

from rdflib.compare import _TripleCanonicalizer


sys.setrecursionlimit(10_000)


def canonicalize_triples(graph: Graph, use_improved: bool):
    return graph.serialize(format='longturtle', use_improved=use_improved)
    # return sorted(
    #     _TripleCanonicalizer(graph, use_improved).canonical_triples(),
    #     key=lambda t: (str(t[0]), str(t[1]), str(t[2]))
    # )


def assert_same_canonicalization(n3_string):
    g = Graph().parse(data=n3_string, format="n3")
    t1 = canonicalize_triples(g, False)
    t2 = canonicalize_triples(g, True)
    assert t1 == t2


@pytest.mark.parametrize("n3_string", [
    # Basic triple
    """
    @prefix : <http://example.org/> .
    :a :b :c .
    """,

    # Single blank node
    """
    @prefix : <http://example.org/> .
    :s :p [ :label "x" ] .
    """,

    # Multiple blank nodes
    """
    @prefix : <http://example.org/> .
    :s :p [ :label "x" ]; :p [ :label "y" ] .
    """,

    # Symmetric structure
    """
    @prefix : <http://example.org/> .
    :s :p [ :q :o1; :r :v ], [ :q :o2; :r :v ] .
    """,

    # Chained blank nodes
    """
    @prefix : <http://example.org/> .
    :a :b [ :c [ :d "x" ] ] .
    """,

    # Cycle with blank nodes
    """
    @prefix : <http://example.org/> .
    _:a :p _:b .
    _:b :p _:a .
    """,

    # Redundant symmetric structure
    """
    @prefix : <http://example.org/> .
    :a :b [ :c :d ]; :b [ :c :d ] .
    """,

    # Identical labels on blank nodes
    """
    @prefix : <http://example.org/> .
    :s :p [ :label "X" ], [ :label "X" ] .
    """,

    # Complex nest with shared URI
    """
    @prefix : <http://example.org/> .
    :s :p [ :a [ :b [ :c :x ] ] ; :x :z ] .
    """,

    # Mixed blank nodes and URIs
    """
    @prefix : <http://example.org/> .
    :a :b :c .
    :a :b [ :c :d ] .
    :a :b [ :c :d ] .
    """,

    # Deep symmetry requiring tie-breaking
    """
    @prefix : <http://example.org/> .
    :s :p [ :a :x; :b :y ], [ :a :x; :b :y ] .
    """,
])
def test_equivalent_canonicalization(n3_string):
    assert_same_canonicalization(n3_string)


def test_determinism():
    """Run canonicalization twice on the same graph and assert deterministic output."""
    n3 = """
    @prefix : <http://example.org/> .
    :s :p [ :a :x; :b :y ], [ :a :x; :b :y ] .
    """
    g = Graph().parse(data=n3, format="n3")
    c1 = canonicalize_triples(g, True)
    c2 = canonicalize_triples(g, True)
    assert c1 == c2


def test_determinism_original():
    """Control: check that the original is deterministic too."""
    n3 = """
    @prefix : <http://example.org/> .
    :s :p [ :a :x; :b :y ], [ :a :x; :b :y ] .
    """
    g = Graph().parse(data=n3, format="n3")
    c1 = canonicalize_triples(g, False)
    c2 = canonicalize_triples(g, True)
    assert c1 == c2

def test_failure_case_exposes_difference():
    """
    This pathological graph has multiple equally scoring colorings
    but only some lead to a full discrete refinement.
    """
    n3 = """
    @prefix : <http://example.org/> .
    :root :connect _:a, _:b, _:c .
    _:a :connect _:b .
    _:b :connect _:c .
    _:c :connect _:a .
    _:a :label "A" .
    _:b :label "A" .
    _:c :label "A" .
    """
    g = Graph().parse(data=n3, format="n3")
    t_original = canonicalize_triples(g, False)
    t_optimized = canonicalize_triples(g, True)
    assert t_original == t_optimized, "Optimized version deviates from original on critical edge case"

def test_performance():
    ntriples = '''
        _:N326fcaa082c24b46b5f11d348e61775b <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:Nb0478247e6e842a8a07613bef4c2390b .
        _:Ncfac004fcdc044ff9bd05a4f96a5d6cd <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435416> .
        _:N62f58c5aebc74afd9ef9efa35aacbdb3 <http://www.cidoc-crm.org/cidoc-crm/P106_is_composed_of> _:N7ac2ff624a324d1d84f7a33274977e50 .
        _:Ne1f77dcd13b94e0cacaa3f647ca7d58d <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "De onderstaande maten zijn de maten van DE GEHELE BETIMMERING. De maten zijn afkomstig uit de documentatie van Aannemingbedrijf J.Kneppers, van offerte/werkvoorstel met werknummer 04/085. Gemaakt tijdens de verhuizing 2003." .
        _:N8c181583a636475f93830394d629094c <http://www.cidoc-crm.org/cidoc-crm/P106_is_composed_of> _:Nb4b2aae9d771492b84fefc048c75ce40 .
        _:N0bd6f8641bfd4752ae8f824aff7758fe <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N7c21cb705a4749f28e6b286c592abd92 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N1c6a400b9d1c4264953b51c48725e82a <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300445022> .
        _:N10991c13ecad4042b6f74897010a2fd5 <http://www.cidoc-crm.org/cidoc-crm/P91_has_unit> <http://vocab.getty.edu/aat/300379098> .
        _:N7acecaf459d14b8ba111553f6a9673b0 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/22011> .
        _:N1cb7a3434e7c4805a84b96fd1cb75cba <http://www.cidoc-crm.org/cidoc-crm/P91_has_unit> <http://vocab.getty.edu/aat/300379098> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N326fcaa082c24b46b5f11d348e61775b .
        _:N439a7b29c632470987ba69c53f6ea05a <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "paneel meest rechts" .
        _:N28dd45fcc8034fce905c95d208d82ee5 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:N09ddaca824f34874be53c19746261aaa <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N6909906c70ae4cba8a159e8b3f35e484 .
        _:Nf15f848ab09a454486a027f9af75f2f0 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300456575> .
        <https://id.rijksmuseum.nl/2202603> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E55_Type> .
        _:N93137abd12e24f8d8a6ae1da855876cd <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/2203> .
        _:Nf0260e9707094511901daf9ab473565a <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:Nb9d8d388a0d740bc883fa0ef3581de24 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:Ne6fb6c600d3e4db5ba6325f7d36203b6 <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N0e02d5ecb0d74c889cd09a38a989ef88 .
        _:N9853680ebb9a422a914744450f06c61d <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:N62f58c5aebc74afd9ef9efa35aacbdb3 <http://www.cidoc-crm.org/cidoc-crm/P106_is_composed_of> _:Na9cacc1829df47ecb369f81d1bc11693 .
        _:N1b3ed30ab1d848b183ae623b1b6f73e8 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:Nca4369bc9b714f04b162701fa9ebb6c0 <http://www.cidoc-crm.org/cidoc-crm/P90_has_value> "5" .
        _:Nedd8d559277c461f9fe13fab7b26450b <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        _:N6f6d1d215da54c718f7bcbf200bdeb70 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:N95bcf74bfc184ed09817d8587821b356 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N572d06b4dd424d299647e1250f8fbc28 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N11f9777424e34080a6f34cddd051c1cf <http://www.cidoc-crm.org/cidoc-crm/P177_assigned_property_of_type> <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> .
        _:N0bd6f8641bfd4752ae8f824aff7758fe <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N3859a270ab8a4f8380f03ab1c0bbccc7 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:N7c21cb705a4749f28e6b286c592abd92 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N8c181583a636475f93830394d629094c <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:N1a462cc9f2b142a3ad30e821b9193592 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N2fdf9d11a66045daafc63715d749a4e4 .
        _:N01be04987df14fdfbb1f874333ae213b <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N971952f14ca64c16877973270227af01 .
        _:N46369579875c4d4993a1e9115e4afd5c <http://www.cidoc-crm.org/cidoc-crm/P90_has_value> "22" .
        _:N0cab1d0fb97a4a58a25c186a712a3276 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:N027a25da94e04bc0bd578b276c45ce92 <http://www.cidoc-crm.org/cidoc-crm/P91_has_unit> <http://vocab.getty.edu/aat/300379098> .
        _:N24f41bf40d8b4e4e9da094b0ac9974c8 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        <https://id.rijksmuseum.nl/22012> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E55_Type> .
        _:N3b2a98dbac624848ac3dd47af776626b <http://www.cidoc-crm.org/cidoc-crm/P177_assigned_property_of_type> <http://www.cidoc-crm.org/cidoc-crm/P15_was_influenced_by> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N7a5d1eaef1a044429136dad2a15c9fac .
        _:N9fac90d69ab74000b3ec6ce5db36a70c <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300456575> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P43_has_dimension> _:N10991c13ecad4042b6f74897010a2fd5 .
        _:N703c95b914c74d59b922c85de28417fe <http://www.cidoc-crm.org/cidoc-crm/P141i_was_assigned_by> _:N6627f4dbe3de4ae9892b257245e18310 .
        _:N9f7bfe219f334214a1fa69b1f708806a <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        _:N62f58c5aebc74afd9ef9efa35aacbdb3 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300311705> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P141i_was_assigned_by> _:Na467b5ec285348b9a5549ba677c13dba .
        <https://id.rijksmuseum.nl/30125375> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:Nd9ddd9258d3a461aa9eb7aac209a5210 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N95bcf74bfc184ed09817d8587821b356 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:Nb71fe9e9d62043b08a97bfea340fe166 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P43_has_dimension> _:N6d361e0d732e413e80b8df766c403fcc .
        _:N6554fa7e891d42f5b2d66091751fdbab <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:Ncf59d64c146f4b54bdf1e2e0d57bfa66 .
        _:N602fd592d77646408d865835ee712135 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "1 x wandsteen (rechthoekig)" .
        _:N3b8054b7b5944f5483da63d105d116ac <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N595302ef02574bce97929841aea079fb .
        _:Nd91c97946f9544deba324bdfa2acf583 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/22026> .
        _:N08a0cc3dd9c54665a6eded9e92a8c5bc <http://www.cidoc-crm.org/cidoc-crm/P141_assigned> _:Nf3e78ce4061f4ba4bc87ece8120be08a .
        _:Na7bfabc7e26645d4bf6702b2a89ebe38 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/22011> .
        _:Nfbbd7c56a7e241ac8565ff0e8a1500d5 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "height 251 cm x width 840 cm" .
        <https://id.rijksmuseum.nl/2201366> <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435443> .
        <http://vocab.getty.edu/aat/300048722> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E55_Type> .
        _:Nf5b24b74e0434c2294e883665c0d01f3 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:N7a5d1eaef1a044429136dad2a15c9fac <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        <https://id.rijksmuseum.nl/200140269> <https://linked.art/ns/terms/member_of> <https://id.rijksmuseum.nl/26139> .
        _:N11f9777424e34080a6f34cddd051c1cf <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300311954> .
        _:N608dde33f09f49f4817df74612a94b78 <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:Nb9d8d388a0d740bc883fa0ef3581de24 .
        _:N28b554b5d861495b9f4272a99abf118c <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "1" .
        _:Na467b5ec285348b9a5549ba677c13dba <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300311954> .
        _:Nfde69f83e1864cada3c4d42e90b0552d <http://www.cidoc-crm.org/cidoc-crm/P106_is_composed_of> _:Na2302e47b8ba46bbba23d0f8ff03a902 .
        <https://id.rijksmuseum.nl/200140269> <https://linked.art/ns/terms/member_of> <https://id.rijksmuseum.nl/260212> .
        _:N37f56317157d4e5292e352fbf1c81916 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:Ncf57d46182e64288b6e551bd7e9c5519 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "instap bedstee" .
        _:N1d8689097c9f4d91b58fc616df41dd2d <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E30_Right> .
        _:N7992374a81c1459da0232a7f66bd5f94 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N5c16dbaa70544c5ca1e482f85099cefc .
        _:N601e00fa88834f91ba480248515ee765 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "1626" .
        _:N93137abd12e24f8d8a6ae1da855876cd <http://www.cidoc-crm.org/cidoc-crm/P90_has_value> "9" .
        _:N2bc47437568e409fb8c222ab6e7be46f <http://www.cidoc-crm.org/cidoc-crm/P82b_end_of_the_end> "2018-02-27T00:00:00Z"^^<http://www.w3.org/2001/XMLSchema#dateTime> .
        _:N33730449371c4173a22a9814bef22a21 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300456575> .
        _:N2ac9912314b0440abca8ea7ad2d0b40f <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        _:N9f04257021c844ad9f03d1cf48540509 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N37f56317157d4e5292e352fbf1c81916 .
        _:N22aa8fbc2b2e47b9b9fea725fad48065 <http://www.cidoc-crm.org/cidoc-crm/P9_consists_of> _:Ne6fb6c600d3e4db5ba6325f7d36203b6 .
        _:Nf65276a3f25d4ade99a6af1dd57092ff <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300404670> .
        _:Nb0478247e6e842a8a07613bef4c2390b <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:Nfd49546aacb1470594f93824a9041c17 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "paneel rechts schouw" .
        _:Na5e61396949640109227da3a437d15fe <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "anonymous, anonymous, anoniem, anoniem" .
        _:N4c863561bde041fcacb50db185059c8a <http://www.cidoc-crm.org/cidoc-crm/P90_has_value> "250" .
        _:N2bc47437568e409fb8c222ab6e7be46f <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:Nd5d6fc8f1f5c4c25950b0592d4b78979 .
        _:N37947258001e4fe886ef5e16ee8d098b <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/22012> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P141i_was_assigned_by> _:N10a54ac58ff24ee0ad919ee913a09098 .
        _:Nf65276a3f25d4ade99a6af1dd57092ff <http://www.cidoc-crm.org/cidoc-crm/P106_is_composed_of> _:Nfde69f83e1864cada3c4d42e90b0552d .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P43_has_dimension> _:N4c863561bde041fcacb50db185059c8a .
        _:N3859a270ab8a4f8380f03ab1c0bbccc7 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        <http://vocab.getty.edu/aat/300417207> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E55_Type> .
        _:N82590e8f23af4251a37c031c32f125dc <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E54_Dimension> .
        _:Ne1f77dcd13b94e0cacaa3f647ca7d58d <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N0ce70c349eb8403a8168e30af15c6b93 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:Nca4369bc9b714f04b162701fa9ebb6c0 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E54_Dimension> .
        <http://hdl.handle.net/10934/RM0001.COLLECT.52172> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E22_Human-Made_Object> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P45_consists_of> <https://id.rijksmuseum.nl/220123> .
        _:Ne6fb6c600d3e4db5ba6325f7d36203b6 <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:Ncfac004fcdc044ff9bd05a4f96a5d6cd .
        _:N2d00c5101f844d34acd31d2b253a4282 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N1ea15331a2a04f61a9e7f549ffe9b8e3 .
        _:N0cea638f6bff4297bfe503fe8669d33b <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P43_has_dimension> _:N434683045bf941e7ae1c3876c356377b .
        _:Nf508696bbaf14889b6996a0620cf4805 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:N483c3aa94f0f4140a3d8c360a284840e <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        _:Nbc6476862fc24fce8871a051a98d8932 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N2d00c5101f844d34acd31d2b253a4282 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:Nb7a53c8fd8d7436094345a156e356e39 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/22012> .
        _:N7f79f5380ec84a009fb337efe323e347 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N15d3ed5dcbf343539b6bafec92e4a3d6 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:Nf1824cd4b39a41f5b5078f64bb063c43 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:N7acecaf459d14b8ba111553f6a9673b0 <http://www.cidoc-crm.org/cidoc-crm/P91_has_unit> <http://vocab.getty.edu/aat/300379098> .
        _:N55b3b20fb44e4d0f93fdd20f05245535 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "length 176 cm" .
        _:N5371ecd19a6b4420b5b0b818c39dc033 <http://www.cidoc-crm.org/cidoc-crm/P106_is_composed_of> _:N8a4cfa4cc6094ec4b4fbb47ac170d1d3 .
        _:N8fcde2458f8a46b19fd7ebc5dbd66191 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P43_has_dimension> _:N608dde33f09f49f4817df74612a94b78 .
        _:N11eedb37d5ea4da598e5e788962d483b <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435417> .
        _:N24f41bf40d8b4e4e9da094b0ac9974c8 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "console schouw" .
        _:Nfcb44b36ba5f4e2e95f6ce192f5e1da6 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        <https://id.rijksmuseum.nl/2205597> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E55_Type> .
        _:N7a5d1eaef1a044429136dad2a15c9fac <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "height 32 cm x height 32 cm" .
        _:Nf4d33be5acfb487182a4cc317eac39f3 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:Ndc9392ef2fd84fd78a5ab569d96a9b8c .
        _:N439a7b29c632470987ba69c53f6ea05a <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:Ne1f2017392124d449f1d5c2b65ed01c2 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:Na2163ebe97c249608fda081dd3ab24a0 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N7acecaf459d14b8ba111553f6a9673b0 <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:Nbe07f34c77ad43998e8b66a13184cfee .
        _:N326fcaa082c24b46b5f11d348e61775b <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:N081d86ce2eb84d278ef8fd2ef77bdf03 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:Na2a8b3c2453e4826b1f8b1ac821736ab <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        <https://id.rijksmuseum.nl/200632800> <https://linked.art/ns/terms/equivalent> <http://hdl.handle.net/10934/RM0001.COLLECT.605247> .
        _:Nf12eee99ea474b61956284e5b4b3e03f <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300456575> .
        _:Nf57ec8fb8c364c9dad7c26971e3e956a <http://www.cidoc-crm.org/cidoc-crm/P106_is_composed_of> _:N430e162d4f5e44f2a83395ebdaeb7eb6 .
        _:Na19ab59d113f41189b70ab80b863ef3f <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:N4ea6864a30394ca09e8e1f8ef3a51a53 <http://www.cidoc-crm.org/cidoc-crm/P91_has_unit> <http://vocab.getty.edu/aat/300379098> .
        _:N98631203d48a407f8c3106a5ea6c1b9a <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300311705> .
        <https://id.rijksmuseum.nl/242140269> <http://www.cidoc-crm.org/cidoc-crm/P4_has_time-span> _:N58dff35c5ffd4a9699ff4d2f9812b5bc .
        _:Nd34ef77968e842e7bc2a73e11504b287 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N3239b8eb4b284ff985aa2718a56b2f1e .
        _:Ne5b410b375df4ebda580183a7ae699d6 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "Betimmering, bestaande uit wandvakken een schoorsteenmantel en bedstee, 1626" .
        _:N434683045bf941e7ae1c3876c356377b <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:Nf5b24b74e0434c2294e883665c0d01f3 .
        _:N82590e8f23af4251a37c031c32f125dc <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:Na2163ebe97c249608fda081dd3ab24a0 .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P129i_is_subject_of> <https://data.rijksmuseum.nl/200140269> .
        _:N09318b67d7404c08bd1417dcd50778f2 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N6c6d3829ad7b40f4b98b8e3f2661b011 .
        _:Nf4d33be5acfb487182a4cc317eac39f3 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N24a73ce7bd9b49c6ba1155d2578dac6a .
        _:N9202e2d866c1493b8a9151b5ee09a968 <http://www.cidoc-crm.org/cidoc-crm/P177_assigned_property_of_type> <http://www.cidoc-crm.org/cidoc-crm/P15_was_influenced_by> .
        _:N482dd2adec334db989fce4e1be63fe68 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "p. 40-42, afb. 34-35" .
        _:N3ad1d58543eb469d8f0644d22387f287 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "Vlaamse invloeden" .
        _:Nbafe8ea81b65469598b2bc9eea31891e <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:N9f7bfe219f334214a1fa69b1f708806a <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        <https://id.rijksmuseum.nl/22021> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E57_Material> .
        _:N7b763e33a1fe4a919a458f76bcffaee4 <http://www.cidoc-crm.org/cidoc-crm/P141i_was_assigned_by> _:N33c97a2c9c244f1c8177e12a8127ab8d .
        _:N0585088e0a45457485e54372541fb56a <http://www.cidoc-crm.org/cidoc-crm/P90_has_value> "840" .
        _:N37947258001e4fe886ef5e16ee8d098b <http://www.cidoc-crm.org/cidoc-crm/P91_has_unit> <http://vocab.getty.edu/aat/300379098> .
        _:Nb412bc5b75614a6b9f89b97a4c6b71e1 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N5d89ec6c9e8e4da5ae945adc33afe621 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/2203> .
        _:N5452c79ad18548d59c42e3844d13a003 <http://www.cidoc-crm.org/cidoc-crm/P90_has_value> "20" .
        _:Nf2aab31ea1b1439790f47ac2d24b974e <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P43_has_dimension> _:Nb7a53c8fd8d7436094345a156e356e39 .
        _:N6909906c70ae4cba8a159e8b3f35e484 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:Nf5b24b74e0434c2294e883665c0d01f3 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:Nc4169ea2b4ce432794ea787e61e94c88 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        <https://id.rijksmuseum.nl/220907> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E57_Material> .
        _:N345d67f33b8443c9aef51ae71ff22990 <http://www.cidoc-crm.org/cidoc-crm/P90_has_value> "38" .
        _:Nedd8d559277c461f9fe13fab7b26450b <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N7e3f01fdf4474b7c83fbc6c8e432231b <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N88631579030b4d5fa8b7dceb90dcc1ca .
        <https://id.rijksmuseum.nl/200140269> <https://linked.art/ns/terms/member_of> <https://id.rijksmuseum.nl/26132> .
        _:Nc5f8aa4aa4714fddadb069e47a3f3e8f <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435416> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N13bc57dedd8e4ef4914cdfbc2e826249 .
        _:Naee0553c2b924efda8b2f48af18f3d93 <http://www.cidoc-crm.org/cidoc-crm/P82a_begin_of_the_begin> "1626-01-01T00:00:00Z"^^<http://www.w3.org/2001/XMLSchema#dateTime> .
        _:Nbd32e6417f644bc4bbe678599a84d9a1 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N1a0866183b184f5bbdec3e1b3c980274 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        _:N11eedb37d5ea4da598e5e788962d483b <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "anonymous" .
        _:Nd5d6fc8f1f5c4c25950b0592d4b78979 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388277> .
        _:N94263c52765547b0b208b79cfa7824b2 <http://www.cidoc-crm.org/cidoc-crm/P177_assigned_property_of_type> <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> .
        _:Nc2ab8d49b551404e9a60d49b2dca3862 <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:Nbd32e6417f644bc4bbe678599a84d9a1 .
        _:N62373814cc20414594e8e2d863115be4 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N27a101c38ecc45a2a456bfb43524f36e <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300404670> .
        _:Na983800a88d945a5a51a6fe0491c3878 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E13_Attribute_Assignment> .
        _:N885109c17a1840c8bc48ebc3a6426581 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:N88e0b897d1b2414f862c73f3ab315dff <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300048722> .
        _:N3e08df9af24c40f58afdcff60e1f30be <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "10" .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/22015> .
        _:N3679ab9f033b4a508bfcf0c4414ff0a8 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "origineel | reproductie" .
        _:Nf65276a3f25d4ade99a6af1dd57092ff <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:Nb9b8092e98f84178b27a2308b5dea23e <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N1ac61619e0104c48bc0939096b9d3d98 .
        _:N7f79f5380ec84a009fb337efe323e347 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:Nf1824cd4b39a41f5b5078f64bb063c43 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300456575> .
        _:Naad832a2d3574eb9934e19146aaf96df <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N7f966aa3fc8f4ceaac4955a7996452b4 .
        <http://vocab.getty.edu/aat/300435429> <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300418049> .
        <https://id.rijksmuseum.nl/202140269> <https://linked.art/ns/terms/digitally_shown_by> <https://id.rijksmuseum.nl/500118801115697826580> .
        _:N8fcde2458f8a46b19fd7ebc5dbd66191 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300456575> .
        _:N326aae03a4974a92953f4f3132f7c866 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "length 166 cm" .
        _:N3e639b13c720410785ae09160f0d8dd4 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:N2ac9912314b0440abca8ea7ad2d0b40f <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N35e44becd20b419593d5ff5efe283bd0 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:N2199894fb15e4d7e82b807925e431e62 <http://www.cidoc-crm.org/cidoc-crm/P106i_forms_part_of> <https://id.rijksmuseum.nl/30125375> .
        _:Nc0730d8c31044cfb88248a7c618c1fe4 <http://www.cidoc-crm.org/cidoc-crm/P177_assigned_property_of_type> <http://www.cidoc-crm.org/cidoc-crm/P15_was_influenced_by> .
        _:N1f052b21ce384a30a45e2679f813b4df <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300379391> .
        _:Nb44a375aa47a499e9387bf65d1bd0f8c <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N2d00c5101f844d34acd31d2b253a4282 .
        _:N439a7b29c632470987ba69c53f6ea05a <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:Nd888db644e0341279e46077c24364912 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:N66ec8a07f33c40ffa762f4b20bbc836c <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435449> .
        _:Ne528a25442df400e9acea4aabf531466 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "Hoofdgebouw" .
        <https://id.rijksmuseum.nl/2202587> <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435443> .
        _:N5452c79ad18548d59c42e3844d13a003 <http://www.cidoc-crm.org/cidoc-crm/P91_has_unit> <http://vocab.getty.edu/aat/300379098> .
        _:Nbe7f9e24a4044ddba9a04c8af14b8cb8 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P43_has_dimension> _:N6554fa7e891d42f5b2d66091751fdbab .
        _:Ne05c7d06eea84c4691999a4d6bf8f4a9 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:Nf5f0b55569a74f31a05f0096b42efe10 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "voetstuk kolom" .
        _:N1a462cc9f2b142a3ad30e821b9193592 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E54_Dimension> .
        _:N77c5f62bfe2b44019d055bd5fbf30d27 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N0585088e0a45457485e54372541fb56a <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E54_Dimension> .
        _:Ncf3c779254b84e9fb3da285617b4e7e7 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N0bd6f8641bfd4752ae8f824aff7758fe <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "paneel meest rechts: hoogte 250 cm (1 x wandpaneel (2 stukjes hout paneel los))" .
        _:Ne03ff39fbb0c40e28a029d5f7d29dcd3 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P140i_was_attributed_by> _:N7e3f01fdf4474b7c83fbc6c8e432231b .
        _:N94263c52765547b0b208b79cfa7824b2 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300311954> .
        _:N7c21cb705a4749f28e6b286c592abd92 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        <http://vocab.getty.edu/aat/300404620> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E55_Type> .
        _:N103d06b66ba34d26bc4071edd23a3385 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E13_Attribute_Assignment> .
        _:N722102f196cd4dd089bc5bf9a40257ca <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P43_has_dimension> _:Na7bfabc7e26645d4bf6702b2a89ebe38 .
        <https://id.rijksmuseum.nl/220149> <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N64ba3c9b868147b8b0d0ff4ed4cd4e73 .
        _:Nd9ddd9258d3a461aa9eb7aac209a5210 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        <https://id.rijksmuseum.nl/2202587> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E55_Type> .
        _:N6b4b28e0287741169a5e817405736a78 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E13_Attribute_Assignment> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/2202587> .
        _:Nce8be56f772b4597a87c3c8886178f39 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        _:N1cb7a3434e7c4805a84b96fd1cb75cba <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N52401e5acd0a4bc5893b1bba3008cbba .
        _:N0cab1d0fb97a4a58a25c186a712a3276 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "1 x wandpaneel" .
        _:Nf3e78ce4061f4ba4bc87ece8120be08a <http://www.cidoc-crm.org/cidoc-crm/P106i_forms_part_of> <https://id.rijksmuseum.nl/30125374> .
        _:Nf0260e9707094511901daf9ab473565a <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "kroonlijst schouw" .
        _:N1a6332eb389645caa5a17dde503440be <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "voetstuk kolom: hoogte 32 cm (1 x voetstuk rechter kolom) x hoogte 32 cm (1 x voetstuk linker kolom)" .
        _:Nbeff3cf5db1548de8f0c6a6b424fe4bb <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E13_Attribute_Assignment> .
        _:Nb7a53c8fd8d7436094345a156e356e39 <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:Nd86696de53aa469b86c73313045ef311 .
        _:Nd8b124c87b204e2ea53d3fbfb970ed65 <http://www.cidoc-crm.org/cidoc-crm/P92_transferred_title_of> <https://id.rijksmuseum.nl/200140269> .
        _:Nbe07f34c77ad43998e8b66a13184cfee <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:Ne5b410b375df4ebda580183a7ae699d6 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300417200> .
        _:N068d3af813a84822a9a10252e1f90654 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N6f6d1d215da54c718f7bcbf200bdeb70 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "height 250 cm" .
        _:Na1779b2ffa7f4b9989aa6b09c4e004d6 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300456575> .
        _:N45abc2b7fbd144e98e4caca8ea712536 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:N054da200073441e0adbbdd9d84fc4568 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/22012> .
        _:N8b8fe726baa048e484b6f096eb04b8c2 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "9" .
        _:N62373814cc20414594e8e2d863115be4 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        <http://vocab.getty.edu/aat/300456575> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E55_Type> .
        <https://id.rijksmuseum.nl/260239> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://linked.art/ns/terms/Set> .
        _:N28b554b5d861495b9f4272a99abf118c <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:N88631579030b4d5fa8b7dceb90dcc1ca <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:Ncf59d64c146f4b54bdf1e2e0d57bfa66 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:Nf65276a3f25d4ade99a6af1dd57092ff <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388277> .
        <http://vocab.getty.edu/aat/300418049> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E55_Type> .
        <https://id.rijksmuseum.nl/202140269> <http://www.cidoc-crm.org/cidoc-crm/P65i_is_shown_by> <https://id.rijksmuseum.nl/200632800> .
        _:N93137abd12e24f8d8a6ae1da855876cd <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N5151ca6daaeb4a48ac8c1a44279166a6 .
        _:Na7bfabc7e26645d4bf6702b2a89ebe38 <http://www.cidoc-crm.org/cidoc-crm/P90_has_value> "80" .
        _:N7b763e33a1fe4a919a458f76bcffaee4 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300456575> .
        _:N483c3aa94f0f4140a3d8c360a284840e <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N1acc4d99a6674bdb9822837fc642ab16 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:N4ea6864a30394ca09e8e1f8ef3a51a53 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E54_Dimension> .
        _:N7ac2ff624a324d1d84f7a33274977e50 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300445022> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P140i_was_attributed_by> _:N9f04257021c844ad9f03d1cf48540509 .
        _:N9853680ebb9a422a914744450f06c61d <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300456575> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P141i_was_assigned_by> _:N94263c52765547b0b208b79cfa7824b2 .
        _:Nca4369bc9b714f04b162701fa9ebb6c0 <http://www.cidoc-crm.org/cidoc-crm/P91_has_unit> <http://vocab.getty.edu/aat/300379098> .
        _:Ndc9392ef2fd84fd78a5ab569d96a9b8c <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        <https://data.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300379475> .
        _:N119d6c758d544f1894f6dd0f34450571 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388277> .
        _:N88631579030b4d5fa8b7dceb90dcc1ca <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "original | reproduction" .
        _:Na9cacc1829df47ecb369f81d1bc11693 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "29" .
        _:N6deccae762f543ff8edc6d030cf85cb1 <http://www.cidoc-crm.org/cidoc-crm/P90_has_value> "40" .
        _:N3679ab9f033b4a508bfcf0c4414ff0a8 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        <https://id.rijksmuseum.nl/200140269> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E22_Human-Made_Object> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P43_has_dimension> _:Nd75a21fffb2f42cbaf123a3a8f6fa3de .
        <https://id.rijksmuseum.nl/301136271> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N5452c79ad18548d59c42e3844d13a003 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N7c1ab7ef63274e8b87a71f557ad956b8 .
        _:Nd86696de53aa469b86c73313045ef311 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:Nf3e78ce4061f4ba4bc87ece8120be08a <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N8c181583a636475f93830394d629094c .
        _:Nab29a88bd6624273b3e69f939bdc43d2 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:N7a5d1eaef1a044429136dad2a15c9fac <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        <https://id.rijksmuseum.nl/2203> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E55_Type> .
        _:N9f04257021c844ad9f03d1cf48540509 <http://www.cidoc-crm.org/cidoc-crm/P141_assigned> <https://id.rijksmuseum.nl/200140262> .
        _:Naad832a2d3574eb9934e19146aaf96df <http://www.cidoc-crm.org/cidoc-crm/P91_has_unit> <http://vocab.getty.edu/aat/300379098> .
        _:N4841974218ed4f44b01113de5a960a2a <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N9f7bfe219f334214a1fa69b1f708806a .
        _:N7987dfeff72a4a079682b0fc0ef2adcc <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N0cea638f6bff4297bfe503fe8669d33b .
        _:N1a0866183b184f5bbdec3e1b3c980274 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:N4bec33370efd46e8a61e1adb740013a9 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "2" .
        _:Nd888db644e0341279e46077c24364912 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "console schouw" .
        _:N0cea638f6bff4297bfe503fe8669d33b <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "1 x plafondpaneel" .
        _:N6b0dee5761c544e7bdca4844a780cac1 <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:Ne1f77dcd13b94e0cacaa3f647ca7d58d .
        _:N7a8f1bd8a5734f2aaf0f1692e26b79e3 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N74c857482c264766ad5f98cabbd270f1 .
        _:N8a4cfa4cc6094ec4b4fbb47ac170d1d3 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300404670> .
        _:N705c4d6a6699417995110eaab1c55117 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        <https://id.rijksmuseum.nl/200140269> <https://linked.art/ns/terms/equivalent> <http://hdl.handle.net/10934/RM0001.COLLECT.52172> .
        _:Ne2e0a6cbff8242cf96b14a719ba4e236 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        <https://id.rijksmuseum.nl/220147> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E57_Material> .
        _:N7c1ab7ef63274e8b87a71f557ad956b8 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:N18477e1a18684649b862535722c3366b <http://www.cidoc-crm.org/cidoc-crm/P141i_was_assigned_by> _:N9202e2d866c1493b8a9151b5ee09a968 .
        _:N28dd45fcc8034fce905c95d208d82ee5 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:Nb542bdb6c71c4f2d8e69c260634d9d07 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:Nb37f04e0249540e194ad05cd81fea8c6 .
        <https://id.rijksmuseum.nl/242140269> <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/22042> .
        _:N1d603ad9502b4f6dbb792ca6713d922c <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E13_Attribute_Assignment> .
        _:Nd5c88d41417c4995bebbfefe3e23aa3f <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E13_Attribute_Assignment> .
        _:Na5e61396949640109227da3a437d15fe <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435416> .
        _:Na4ed40dc21804706b623189d751b6fd1 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N9e29bd1609c242668d0b27932fcfea8d .
        _:Naee0553c2b924efda8b2f48af18f3d93 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N09f93d0f42bc47a48d8f98adf5aa17ab .
        <https://id.rijksmuseum.nl/2202215> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E55_Type> .
        _:Nc2b555ca9f6f41388073becf10aea022 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "7" .
        _:Nce8be56f772b4597a87c3c8886178f39 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:N82590e8f23af4251a37c031c32f125dc <http://www.cidoc-crm.org/cidoc-crm/P91_has_unit> <http://vocab.getty.edu/aat/300379098> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P45_consists_of> <https://id.rijksmuseum.nl/2205125> .
        _:N4bec33370efd46e8a61e1adb740013a9 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300456575> .
        _:Nd295802bf45949a99e46328665a91c1c <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        <http://vocab.getty.edu/aat/300435449> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E55_Type> .
        _:N88631579030b4d5fa8b7dceb90dcc1ca <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388277> .
        _:N66ec8a07f33c40ffa762f4b20bbc836c <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388277> .
        _:N59a34bd195db4121918f1827bdfbf755 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:N68141ab26c3c49509b68406b177ee851 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        <https://id.rijksmuseum.nl/2202215> <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435443> .
        _:Ne6c70d7bc3994992a5e7cb760221e390 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300456575> .
        _:N8a4cfa4cc6094ec4b4fbb47ac170d1d3 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "Wandbetimmering met schoorsteenmantel, wandvakken en een portiek" .
        _:N054da200073441e0adbbdd9d84fc4568 <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:Nedd8d559277c461f9fe13fab7b26450b .
        _:N601e00fa88834f91ba480248515ee765 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:N0880a231761441dcbb57606e8decb557 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N2610e69ebd804846b591e4014a84fdc8 .
        _:Ne528a25442df400e9acea4aabf531466 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N09412cb461ed4f19bb7390358576be19 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "plafond bedstee" .
        _:N9e29bd1609c242668d0b27932fcfea8d <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:Nbafe8ea81b65469598b2bc9eea31891e <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        _:N1ea15331a2a04f61a9e7f549ffe9b8e3 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:N32a1df65f52342f28aefb91dc9064ede <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        <https://data.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P104_is_subject_to> _:N1d8689097c9f4d91b58fc616df41dd2d .
        _:N1caa6709b1554c4dbf1ef2a03c7a74fd <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:Nb0478247e6e842a8a07613bef4c2390b <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300456575> .
        _:N58dff35c5ffd4a9699ff4d2f9812b5bc <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E52_Time-Span> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P43_has_dimension> _:N7acecaf459d14b8ba111553f6a9673b0 .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N6f6d1d215da54c718f7bcbf200bdeb70 .
        <https://id.rijksmuseum.nl/22015218> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E55_Type> .
        <https://id.rijksmuseum.nl/22021> <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N7b763e33a1fe4a919a458f76bcffaee4 .
        <https://id.rijksmuseum.nl/230171> <https://linked.art/ns/terms/equivalent> <http://vocab.getty.edu/tgn/7006798> .
        _:Necea879225e24b18affc4d99504cb152 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:Na983800a88d945a5a51a6fe0491c3878 <http://www.cidoc-crm.org/cidoc-crm/P177_assigned_property_of_type> <http://www.cidoc-crm.org/cidoc-crm/P15_was_influenced_by> .
        _:N64ba3c9b868147b8b0d0ff4ed4cd4e73 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "5" .
        _:N3679ab9f033b4a508bfcf0c4414ff0a8 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N64d5dc3e891a4d63abf4c0599b6b01e6 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:Nc02025eb8dac4dce94feba87e938d55c .
        <https://id.rijksmuseum.nl/200140269> <https://linked.art/ns/terms/member_of> <https://id.rijksmuseum.nl/260239> .
        _:N32208ec5b9ce4b838a0d90897c98480f <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:Ne05c7d06eea84c4691999a4d6bf8f4a9 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "5" .
        _:N77c5f62bfe2b44019d055bd5fbf30d27 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "height 115 cm x height 115 cm" .
        _:Nb37f04e0249540e194ad05cd81fea8c6 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:N55b3b20fb44e4d0f93fdd20f05245535 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:Ne05c7d06eea84c4691999a4d6bf8f4a9 .
        <http://vocab.getty.edu/aat/300311705> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E55_Type> .
        <http://vocab.getty.edu/aat/300388256> <http://www.w3.org/2000/01/rdf-schema#label> "Dutch" .
        _:N2bc47437568e409fb8c222ab6e7be46f <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E52_Time-Span> .
        _:Nc4169ea2b4ce432794ea787e61e94c88 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:Nc21e4df26d3f4c409540c3d9882f7a2c <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/22012> .
        _:N6f6d1d215da54c718f7bcbf200bdeb70 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:Nb44a375aa47a499e9387bf65d1bd0f8c <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N434683045bf941e7ae1c3876c356377b <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/22011> .
        _:N18477e1a18684649b862535722c3366b <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "4" .
        _:Nd91c97946f9544deba324bdfa2acf583 <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:Nfcb44b36ba5f4e2e95f6ce192f5e1da6 .
        _:N8a4cfa4cc6094ec4b4fbb47ac170d1d3 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:Nc02025eb8dac4dce94feba87e938d55c <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:N6deccae762f543ff8edc6d030cf85cb1 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/22011> .
        _:Ne1f2017392124d449f1d5c2b65ed01c2 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:N616b457f812f4e1696ba92dd99bc1989 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E54_Dimension> .
        _:Na2163ebe97c249608fda081dd3ab24a0 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:N4ea6864a30394ca09e8e1f8ef3a51a53 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/22011> .
        <https://id.rijksmuseum.nl/26132> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://linked.art/ns/terms/Set> .
        _:N46369579875c4d4993a1e9115e4afd5c <http://www.cidoc-crm.org/cidoc-crm/P91_has_unit> <http://vocab.getty.edu/aat/300379098> .
        _:N326aae03a4974a92953f4f3132f7c866 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:N1f3bcdeb3f524aa996b98fc3dce46a9c <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N37f56317157d4e5292e352fbf1c81916 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "related object" .
        _:N6c6d3829ad7b40f4b98b8e3f2661b011 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300404670> .
        _:Nf508696bbaf14889b6996a0620cf4805 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300456575> .
        _:N28dd45fcc8034fce905c95d208d82ee5 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:Naee0553c2b924efda8b2f48af18f3d93 <http://www.cidoc-crm.org/cidoc-crm/P82b_end_of_the_end> "1626-12-31T23:59:59Z"^^<http://www.w3.org/2001/XMLSchema#dateTime> .
        _:Nf57ec8fb8c364c9dad7c26971e3e956a <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300311705> .
        _:N0cea638f6bff4297bfe503fe8669d33b <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:Nfcb44b36ba5f4e2e95f6ce192f5e1da6 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "1 x zijwand bedstee (instap bedstee)" .
        _:N48d792fead8e4090a0ad284334194246 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/22012> .
        _:N3e639b13c720410785ae09160f0d8dd4 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        _:Nb362ca7497fe44d5bebcd2e665a7c9d3 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:N326fcaa082c24b46b5f11d348e61775b <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "0" .
        _:N35e44becd20b419593d5ff5efe283bd0 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        <https://creativecommons.org/publicdomain/mark/1.0/> <http://www.w3.org/2000/01/rdf-schema#label> "Public Domain" .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P43_has_dimension> _:N5d89ec6c9e8e4da5ae945adc33afe621 .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:Nb0062b0bf6ad47fa9357e4598b8dc73f .
        _:N7e277d258b834c0f80be80cb95562238 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388277> .
        _:N1a462cc9f2b142a3ad30e821b9193592 <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N95bcf74bfc184ed09817d8587821b356 .
        <https://id.rijksmuseum.nl/220123> <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N703c95b914c74d59b922c85de28417fe .
        _:N3b8054b7b5944f5483da63d105d116ac <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E54_Dimension> .
        _:N01be04987df14fdfbb1f874333ae213b <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "width 132.5 cm x width 133.5 cm x width 60 cm x depth 11 cm x width 110 cm x depth 5 cm x width 173 cm x depth 5 cm x width 73 cm x depth 5 cm x width 250 cm x depth 80 cm x width 22 cm x depth 60 cm x width 15 cm x depth 15 cm x width 20 cm x depth 9 cm x width 20 cm x depth 38 cm x width 22 cm x depth 60 cm x width 20 cm x depth 9 cm x width 30 cm x depth 38 cm" .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P55_has_current_location> _:N09318b67d7404c08bd1417dcd50778f2 .
        _:N602fd592d77646408d865835ee712135 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P43_has_dimension> _:N7987dfeff72a4a079682b0fc0ef2adcc .
        _:N1a462cc9f2b142a3ad30e821b9193592 <http://www.cidoc-crm.org/cidoc-crm/P91_has_unit> <http://vocab.getty.edu/aat/300379098> .
        _:N1f052b21ce384a30a45e2679f813b4df <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:N658aff6bbc4d45db8b4b42450712f00e <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:N66ec8a07f33c40ffa762f4b20bbc836c <http://www.cidoc-crm.org/cidoc-crm/P106_is_composed_of> _:N1f052b21ce384a30a45e2679f813b4df .
        _:N11eedb37d5ea4da598e5e788962d483b <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N1f3bcdeb3f524aa996b98fc3dce46a9c <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N3e185a0c0020413da970158c34c0d4cd <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:Nf12eee99ea474b61956284e5b4b3e03f <http://www.cidoc-crm.org/cidoc-crm/P141i_was_assigned_by> _:N103d06b66ba34d26bc4071edd23a3385 .
        _:N3c674b37f0574fc19bf820b10b42d812 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:Ncf3c779254b84e9fb3da285617b4e7e7 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:N3c1023bca87d4df3afb4a17c87a21236 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N8a4cfa4cc6094ec4b4fbb47ac170d1d3 .
        _:N32a1df65f52342f28aefb91dc9064ede <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N70dd4554fd0445d5a0c1211e79eb5b53 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388277> .
        _:N15d3ed5dcbf343539b6bafec92e4a3d6 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N8b8fe726baa048e484b6f096eb04b8c2 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300456575> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P43_has_dimension> _:N46369579875c4d4993a1e9115e4afd5c .
        _:Nb4b2aae9d771492b84fefc048c75ce40 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "afb. XI-XII" .
        _:N2ac9912314b0440abca8ea7ad2d0b40f <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:Nf7dbe80f8d4b46d680024f9ab39b50e6 <http://www.cidoc-crm.org/cidoc-crm/P141_assigned> <https://id.rijksmuseum.nl/200140269> .
        _:Nf2aab31ea1b1439790f47ac2d24b974e <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300456575> .
        _:N64ba3c9b868147b8b0d0ff4ed4cd4e73 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300456575> .
        _:N93137abd12e24f8d8a6ae1da855876cd <http://www.cidoc-crm.org/cidoc-crm/P91_has_unit> <http://vocab.getty.edu/aat/300379098> .
        _:N6909906c70ae4cba8a159e8b3f35e484 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300456575> .
        _:N8a4cfa4cc6094ec4b4fbb47ac170d1d3 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N2bcf69baf4334e1bb1ebfba3e5a96afc <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E54_Dimension> .
        _:N6c6d3829ad7b40f4b98b8e3f2661b011 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:N103d06b66ba34d26bc4071edd23a3385 <http://www.cidoc-crm.org/cidoc-crm/P177_assigned_property_of_type> <http://www.cidoc-crm.org/cidoc-crm/P15_was_influenced_by> .
        _:Nb7490660783349da8c8f3584b200fdb1 <http://www.cidoc-crm.org/cidoc-crm/P141_assigned> _:N572d06b4dd424d299647e1250f8fbc28 .
        _:N98631203d48a407f8c3106a5ea6c1b9a <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "Documentatiemap." .
        _:N2610e69ebd804846b591e4014a84fdc8 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:N326fcaa082c24b46b5f11d348e61775b <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N0880a231761441dcbb57606e8decb557 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N5151ca6daaeb4a48ac8c1a44279166a6 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N55b3b20fb44e4d0f93fdd20f05245535 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388277> .
        _:N5371ecd19a6b4420b5b0b818c39dc033 <http://www.cidoc-crm.org/cidoc-crm/P106_is_composed_of> _:N6b20b0bc4ce8442f87e5e14187a5e606 .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P43_has_dimension> _:Ncd301494c82849caba4115a0d298fade .
        _:N77c5f62bfe2b44019d055bd5fbf30d27 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:Na19ab59d113f41189b70ab80b863ef3f <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N48d792fead8e4090a0ad284334194246 <http://www.cidoc-crm.org/cidoc-crm/P91_has_unit> <http://vocab.getty.edu/aat/300379098> .
        _:N80a9d20c250c4bf98625378781048e22 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:Nd0da0cd3b0bf4e04833992add79cd921 .
        _:Ndbb8fc769442469c89fcfafae4d956d3 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:N616b457f812f4e1696ba92dd99bc1989 <http://www.cidoc-crm.org/cidoc-crm/P90_has_value> "11" .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P45_consists_of> <https://id.rijksmuseum.nl/22021> .
        <http://vocab.getty.edu/tgn/7006798> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E53_Place> .
        _:Nfde69f83e1864cada3c4d42e90b0552d <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P43_has_dimension> _:N1cb7a3434e7c4805a84b96fd1cb75cba .
        _:N595302ef02574bce97929841aea079fb <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        _:Nc2b555ca9f6f41388073becf10aea022 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300456575> .
        _:N5492ef60c35c4f5d9f3bc23f6117c9ba <http://www.cidoc-crm.org/cidoc-crm/P4_has_time-span> _:N2bc47437568e409fb8c222ab6e7be46f .
        _:N187de5db104b498285561e41ac556499 <http://www.cidoc-crm.org/cidoc-crm/P90_has_value> "80" .
        _:Naecfa816892c49c38a92d7eadfa75ae4 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N602fd592d77646408d865835ee712135 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N6d31805660c34ca194154a5df206a7de <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        <https://id.rijksmuseum.nl/2201073> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E55_Type> .
        _:N17e116ac376c41eeaa1884c0e5713ca5 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N08a0cc3dd9c54665a6eded9e92a8c5bc <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300311954> .
        _:N33c97a2c9c244f1c8177e12a8127ab8d <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E13_Attribute_Assignment> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P43_has_dimension> _:N48d792fead8e4090a0ad284334194246 .
        _:Na19ab59d113f41189b70ab80b863ef3f <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "conform cat. 1952" .
        _:N01be04987df14fdfbb1f874333ae213b <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:N33c97a2c9c244f1c8177e12a8127ab8d <http://www.cidoc-crm.org/cidoc-crm/P141_assigned> <https://id.rijksmuseum.nl/200140269> .
        _:N658aff6bbc4d45db8b4b42450712f00e <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N10a54ac58ff24ee0ad919ee913a09098 <http://www.cidoc-crm.org/cidoc-crm/P141_assigned> _:Nf41ddfb3b37748b1855b424b6032fe40 .
        _:N1caa6709b1554c4dbf1ef2a03c7a74fd <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "gerelateerd object" .
        _:Naad832a2d3574eb9934e19146aaf96df <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/22011> .
        _:N5dd0d1de24294ec5a2b1f9b4c025be51 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        <https://id.rijksmuseum.nl/2201073> <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435443> .
        _:N703c95b914c74d59b922c85de28417fe <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300456575> .
        _:N082f41fa1877442bb605fceb4dab9da7 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:Na19ab59d113f41189b70ab80b863ef3f <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:Nc2555581e07b470f9ae3c85d2c5bc75f <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        _:Ne6fb6c600d3e4db5ba6325f7d36203b6 <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N068d3af813a84822a9a10252e1f90654 .
        _:N74c857482c264766ad5f98cabbd270f1 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:N6c6d3829ad7b40f4b98b8e3f2661b011 <http://www.cidoc-crm.org/cidoc-crm/P106_is_composed_of> _:Ne528a25442df400e9acea4aabf531466 .
        _:Nd5c88d41417c4995bebbfefe3e23aa3f <http://www.cidoc-crm.org/cidoc-crm/P177_assigned_property_of_type> <http://www.cidoc-crm.org/cidoc-crm/P15_was_influenced_by> .
        _:N053403eb2d9e45f99f1da036db71b1ee <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388277> .
        _:Ne2e0a6cbff8242cf96b14a719ba4e236 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        _:N0cb07388ba2a4f8c8344bfb6e024f3bc <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N0ce70c349eb8403a8168e30af15c6b93 .
        _:N7c1ab7ef63274e8b87a71f557ad956b8 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        _:Na2a8b3c2453e4826b1f8b1ac821736ab <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300311705> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P45_consists_of> <https://id.rijksmuseum.nl/220907> .
        _:N1d603ad9502b4f6dbb792ca6713d922c <http://www.cidoc-crm.org/cidoc-crm/P141_assigned> _:Na2e28bbaa6ed4a4cab5c09738fd06bfa .
        _:N3f0071080f814903b65c8093e0b87567 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N971952f14ca64c16877973270227af01 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "4" .
        _:N0bd6f8641bfd4752ae8f824aff7758fe <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:Nc2b555ca9f6f41388073becf10aea022 .
        _:N32208ec5b9ce4b838a0d90897c98480f <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "p. 41" .
        _:Nb542bdb6c71c4f2d8e69c260634d9d07 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E54_Dimension> .
        _:N62f58c5aebc74afd9ef9efa35aacbdb3 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:Ncf57d46182e64288b6e551bd7e9c5519 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N3ad1d58543eb469d8f0644d22387f287 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:Nbd1e5854266f4be8971af77ce121fe39 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N0cd9a3d62b8a4d2eb55832a64919dfdd <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:N2b43b56170b14dd3914425a5e264d3c8 <http://www.cidoc-crm.org/cidoc-crm/P94i_was_created_by> _:N5492ef60c35c4f5d9f3bc23f6117c9ba .
        _:Na4ed40dc21804706b623189d751b6fd1 <http://www.cidoc-crm.org/cidoc-crm/P106i_forms_part_of> <https://id.rijksmuseum.nl/301136271> .
        _:Nf68b0b2a16044b53901390eed14c6ad3 <http://www.cidoc-crm.org/cidoc-crm/P106i_forms_part_of> <https://id.rijksmuseum.nl/30125657> .
        _:N17e116ac376c41eeaa1884c0e5713ca5 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:Na5e61396949640109227da3a437d15fe <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:Ncd301494c82849caba4115a0d298fade <http://www.cidoc-crm.org/cidoc-crm/P90_has_value> "5" .
        _:N483c3aa94f0f4140a3d8c360a284840e <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:N3bbcf21a24c742db8dc5f96f96589c3a <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:Nca4369bc9b714f04b162701fa9ebb6c0 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:Ne03ff39fbb0c40e28a029d5f7d29dcd3 .
        _:Nd91c97946f9544deba324bdfa2acf583 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:Ncf57d46182e64288b6e551bd7e9c5519 .
        _:N46e350cf3cb44e98a607d8f54ea4f04c <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:Nc2ab8d49b551404e9a60d49b2dca3862 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E54_Dimension> .
        _:Nd75a21fffb2f42cbaf123a3a8f6fa3de <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:Nb362ca7497fe44d5bebcd2e665a7c9d3 .
        _:N64ba3c9b868147b8b0d0ff4ed4cd4e73 <http://www.cidoc-crm.org/cidoc-crm/P141i_was_assigned_by> _:Na983800a88d945a5a51a6fe0491c3878 .
        _:N88e0b897d1b2414f862c73f3ab315dff <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:Nb7a53c8fd8d7436094345a156e356e39 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:Nccfaeb94540c4421ab4975acb489d11f .
        _:N95bcf74bfc184ed09817d8587821b356 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:N93137abd12e24f8d8a6ae1da855876cd <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E54_Dimension> .
        _:Nc21e4df26d3f4c409540c3d9882f7a2c <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E54_Dimension> .
        _:Nccfaeb94540c4421ab4975acb489d11f <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        <http://vocab.getty.edu/aat/300404670> <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300418049> .
        _:N09318b67d7404c08bd1417dcd50778f2 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N66ec8a07f33c40ffa762f4b20bbc836c .
        _:N6909906c70ae4cba8a159e8b3f35e484 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "12" .
        _:N28b554b5d861495b9f4272a99abf118c <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300456575> .
        _:N4841974218ed4f44b01113de5a960a2a <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/2203> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P65_shows_visual_item> <https://id.rijksmuseum.nl/202140269> .
        _:Nf65276a3f25d4ade99a6af1dd57092ff <http://www.cidoc-crm.org/cidoc-crm/P94i_was_created_by> _:N5492ef60c35c4f5d9f3bc23f6117c9ba .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P43_has_dimension> _:N027a25da94e04bc0bd578b276c45ce92 .
        _:N48d792fead8e4090a0ad284334194246 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E54_Dimension> .
        <http://vocab.getty.edu/aat/300417200> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E55_Type> .
        _:Nf15f848ab09a454486a027f9af75f2f0 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "8" .
        _:N3c674b37f0574fc19bf820b10b42d812 <http://www.cidoc-crm.org/cidoc-crm/P141i_was_assigned_by> _:Nd5c88d41417c4995bebbfefe3e23aa3f .
        _:Ncf59d64c146f4b54bdf1e2e0d57bfa66 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N6554fa7e891d42f5b2d66091751fdbab <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:Nf5f0b55569a74f31a05f0096b42efe10 .
        _:N64d5dc3e891a4d63abf4c0599b6b01e6 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "wandsteen kolom: hoogte 115 cm (1 x wandsteen (rechthoekig)) x hoogte 115 cm (1 x wandsteen kolom (rechthoekig), aan onderzijde gebroken)" .
        _:N09ddaca824f34874be53c19746261aaa <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:N1b3ed30ab1d848b183ae623b1b6f73e8 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388277> .
        _:Na2e28bbaa6ed4a4cab5c09738fd06bfa <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:Ne6fb6c600d3e4db5ba6325f7d36203b6 <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:Nc5f8aa4aa4714fddadb069e47a3f3e8f .
        _:N6627f4dbe3de4ae9892b257245e18310 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E13_Attribute_Assignment> .
        _:N13bc57dedd8e4ef4914cdfbc2e826249 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N9d83116074a84c1aba09f08548b4b6a6 .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N55b3b20fb44e4d0f93fdd20f05245535 .
        _:N6d31805660c34ca194154a5df206a7de <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N3b8054b7b5944f5483da63d105d116ac <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/22012> .
        _:Nb82f1f80a4d346b99f2a8fb69c43ca29 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:Nfebc8f394dae453391d1161bc0a9c8c0 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "HG-2.4" .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N1a6332eb389645caa5a17dde503440be .
        _:N6b4b28e0287741169a5e817405736a78 <http://www.cidoc-crm.org/cidoc-crm/P177_assigned_property_of_type> <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> .
        _:N5a1cb55c4e164ddca0ebb0b8f6d0a743 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N434683045bf941e7ae1c3876c356377b <http://www.cidoc-crm.org/cidoc-crm/P90_has_value> "251" .
        _:Nbeff3cf5db1548de8f0c6a6b424fe4bb <http://www.cidoc-crm.org/cidoc-crm/P177_assigned_property_of_type> <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> .
        <http://vocab.getty.edu/aat/300435443> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E55_Type> .
        _:Nd34ef77968e842e7bc2a73e11504b287 <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:Nb0899e1f3dcc40beaa1962cb3009fc91 .
        _:Ne5b410b375df4ebda580183a7ae699d6 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        <https://id.rijksmuseum.nl/30125374> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N8a4cfa4cc6094ec4b4fbb47ac170d1d3 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300417207> .
        _:Nf2aab31ea1b1439790f47ac2d24b974e <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "4" .
        _:Nd34ef77968e842e7bc2a73e11504b287 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E54_Dimension> .
        _:Nb0478247e6e842a8a07613bef4c2390b <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "2" .
        _:N2b43b56170b14dd3914425a5e264d3c8 <http://www.cidoc-crm.org/cidoc-crm/P106_is_composed_of> _:N5371ecd19a6b4420b5b0b818c39dc033 .
        _:Nb7476f387a964cc885ceba968cdf3f6a <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N0cea638f6bff4297bfe503fe8669d33b <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:N10a54ac58ff24ee0ad919ee913a09098 <http://www.cidoc-crm.org/cidoc-crm/P177_assigned_property_of_type> <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> .
        _:N572d06b4dd424d299647e1250f8fbc28 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N98631203d48a407f8c3106a5ea6c1b9a .
        _:N372342e34bde4672836392b9ea4bcfac <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N82cc48ea181f4b719a5df1a66123dc02 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        _:N08a0cc3dd9c54665a6eded9e92a8c5bc <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E13_Attribute_Assignment> .
        _:N1acc4d99a6674bdb9822837fc642ab16 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:Necea879225e24b18affc4d99504cb152 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "3" .
        _:Ncf57d46182e64288b6e551bd7e9c5519 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:N93137abd12e24f8d8a6ae1da855876cd <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:Nc4169ea2b4ce432794ea787e61e94c88 .
        <https://id.rijksmuseum.nl/22026> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E55_Type> .
        _:Nfde69f83e1864cada3c4d42e90b0552d <http://www.cidoc-crm.org/cidoc-crm/P106_is_composed_of> _:Nc4ddfca1ccc14e5eb07dd27528790a0d .
        _:Nbd1e5854266f4be8971af77ce121fe39 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:N7f966aa3fc8f4ceaac4955a7996452b4 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:Nb9b8092e98f84178b27a2308b5dea23e <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:Nbe07f34c77ad43998e8b66a13184cfee <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P43_has_dimension> _:N054da200073441e0adbbdd9d84fc4568 .
        _:N1a6332eb389645caa5a17dde503440be <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N71f9d7c8591b43fea200c2f20153243e .
        _:N9e29bd1609c242668d0b27932fcfea8d <http://www.cidoc-crm.org/cidoc-crm/P106_is_composed_of> _:N32208ec5b9ce4b838a0d90897c98480f .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P141i_was_assigned_by> _:N1d603ad9502b4f6dbb792ca6713d922c .
        _:Nb542bdb6c71c4f2d8e69c260634d9d07 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/22011> .
        _:Ne6fb6c600d3e4db5ba6325f7d36203b6 <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:Na5f8e89eb41442b2a53885a6630913b7 .
        _:Nd86696de53aa469b86c73313045ef311 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N47f956f64efc4a91a391e3f6cde786f6 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "BK-NM-3931-B" .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P141i_was_assigned_by> _:N11f9777424e34080a6f34cddd051c1cf .
        _:N3fa85c9e0991441ead5f544faf65e1c9 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:Ne1f77dcd13b94e0cacaa3f647ca7d58d <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:N58dff35c5ffd4a9699ff4d2f9812b5bc <http://www.cidoc-crm.org/cidoc-crm/P82b_end_of_the_end> "1877-12-31T23:59:59Z"^^<http://www.w3.org/2001/XMLSchema#dateTime> .
        _:N4841974218ed4f44b01113de5a960a2a <http://www.cidoc-crm.org/cidoc-crm/P90_has_value> "9" .
        _:Nc2555581e07b470f9ae3c85d2c5bc75f <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:N541427f2d233458e9bc8084d00f36fc3 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N705c4d6a6699417995110eaab1c55117 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N9ac58a8171204af78d71afbe70364eab <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "13" .
        <https://id.rijksmuseum.nl/301151248> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N09ddaca824f34874be53c19746261aaa <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:Nf12eee99ea474b61956284e5b4b3e03f <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:N5a1cb55c4e164ddca0ebb0b8f6d0a743 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "2018-02-27" .
        _:Nd9ddd9258d3a461aa9eb7aac209a5210 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        _:N1ac61619e0104c48bc0939096b9d3d98 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:N3b8054b7b5944f5483da63d105d116ac <http://www.cidoc-crm.org/cidoc-crm/P91_has_unit> <http://vocab.getty.edu/aat/300379098> .
        _:N2bcf69baf4334e1bb1ebfba3e5a96afc <http://www.cidoc-crm.org/cidoc-crm/P91_has_unit> <http://vocab.getty.edu/aat/300379098> .
        _:Nb82f1f80a4d346b99f2a8fb69c43ca29 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N053403eb2d9e45f99f1da036db71b1ee .
        _:N74c857482c264766ad5f98cabbd270f1 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "2018-02-27" .
        _:N1d603ad9502b4f6dbb792ca6713d922c <http://www.cidoc-crm.org/cidoc-crm/P177_assigned_property_of_type> <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> .
        _:N054da200073441e0adbbdd9d84fc4568 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:Nce8be56f772b4597a87c3c8886178f39 .
        _:N6d361e0d732e413e80b8df766c403fcc <http://www.cidoc-crm.org/cidoc-crm/P91_has_unit> <http://vocab.getty.edu/aat/300379098> .
        _:N722102f196cd4dd089bc5bf9a40257ca <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:N80a9d20c250c4bf98625378781048e22 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E54_Dimension> .
        _:N7987dfeff72a4a079682b0fc0ef2adcc <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N09412cb461ed4f19bb7390358576be19 .
        _:N187de5db104b498285561e41ac556499 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/2203> .
        _:Nb412bc5b75614a6b9f89b97a4c6b71e1 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300379391> .
        _:N971952f14ca64c16877973270227af01 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300456575> .
        _:N68141ab26c3c49509b68406b177ee851 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:Nc5f8aa4aa4714fddadb069e47a3f3e8f <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N705c4d6a6699417995110eaab1c55117 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:Nc02025eb8dac4dce94feba87e938d55c <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "13" .
        _:Nb606016b3c3a43668276a89000e202fc <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        <http://vocab.getty.edu/aat/300435452> <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300418049> .
        _:N24f41bf40d8b4e4e9da094b0ac9974c8 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N9ac58a8171204af78d71afbe70364eab <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:N430e162d4f5e44f2a83395ebdaeb7eb6 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:N3239b8eb4b284ff985aa2718a56b2f1e <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:N98631203d48a407f8c3106a5ea6c1b9a <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:Nf24b745418814730b2b21f19f5ab63ec <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P45_consists_of> <https://id.rijksmuseum.nl/220400> .
        _:N053403eb2d9e45f99f1da036db71b1ee <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:N1acc4d99a6674bdb9822837fc642ab16 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N52401e5acd0a4bc5893b1bba3008cbba <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        _:Nbc6476862fc24fce8871a051a98d8932 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:Nd5d6fc8f1f5c4c25950b0592d4b78979 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:N1ea15331a2a04f61a9e7f549ffe9b8e3 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "10" .
        _:N3239b8eb4b284ff985aa2718a56b2f1e <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "voetstuk kolom" .
        _:N24a73ce7bd9b49c6ba1155d2578dac6a <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "Public Domain" .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P108i_was_produced_by> _:N22aa8fbc2b2e47b9b9fea725fad48065 .
        _:N1cb7a3434e7c4805a84b96fd1cb75cba <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/22012> .
        _:N7f79f5380ec84a009fb337efe323e347 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:N5c16dbaa70544c5ca1e482f85099cefc <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:N5d861f12afca43e9879bd7bab9b16288 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "anoniem" .
        <https://id.rijksmuseum.nl/22042> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E55_Type> .
        _:N068d3af813a84822a9a10252e1f90654 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435417> .
        _:Nd34ef77968e842e7bc2a73e11504b287 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/22011> .
        _:N59a34bd195db4121918f1827bdfbf755 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "2.4" .
        _:Nb9b8092e98f84178b27a2308b5dea23e <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N37947258001e4fe886ef5e16ee8d098b <http://www.cidoc-crm.org/cidoc-crm/P90_has_value> "22" .
        _:N88e0b897d1b2414f862c73f3ab315dff <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "Deze betimmering is afkomstig uit een huis in Dordrecht. De opbouw volgt de regels van de klassieke bouwkunst, met zuilen die een fries en een kroonlijst dragen. Het inlegwerk in verschillende houtsoorten verlevendigt de wand. De doorlopende betimmering gaf een vertrek eenheid en voornaamheid, maar isoleerde ook tegen kou en vocht." .
        _:N2610e69ebd804846b591e4014a84fdc8 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300456575> .
        _:Ne359204a393a4afeaeb69ed89ea83ded <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:Nedd8d559277c461f9fe13fab7b26450b <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:N608dde33f09f49f4817df74612a94b78 <http://www.cidoc-crm.org/cidoc-crm/P90_has_value> "73" .
        _:Nd34ef77968e842e7bc2a73e11504b287 <http://www.cidoc-crm.org/cidoc-crm/P90_has_value> "32" .
        _:Nd86696de53aa469b86c73313045ef311 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        <http://hdl.handle.net/10934/RM0001.COLLECT.605247> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E22_Human-Made_Object> .
        _:N2fdf9d11a66045daafc63715d749a4e4 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        _:Nb0899e1f3dcc40beaa1962cb3009fc91 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "1 x voetstuk rechter kolom" .
        _:N1b3ed30ab1d848b183ae623b1b6f73e8 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:Nf508696bbaf14889b6996a0620cf4805 .
        _:N3c1023bca87d4df3afb4a17c87a21236 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435429> .
        <https://id.rijksmuseum.nl/200632800> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E22_Human-Made_Object> .
        _:Nc9bb1c958c024f86bed9da3b7c8724fd <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300456575> .
        _:N3fa85c9e0991441ead5f544faf65e1c9 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        <https://id.rijksmuseum.nl/242140269> <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300055863> .
        _:N3c674b37f0574fc19bf820b10b42d812 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300456575> .
        _:Nb542bdb6c71c4f2d8e69c260634d9d07 <http://www.cidoc-crm.org/cidoc-crm/P91_has_unit> <http://vocab.getty.edu/aat/300379098> .
        _:N9202e2d866c1493b8a9151b5ee09a968 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E13_Attribute_Assignment> .
        _:Nb33e6c41d95f4ecc964e87baf318bb30 <http://www.cidoc-crm.org/cidoc-crm/P141_assigned> <https://id.rijksmuseum.nl/200140269> .
        _:N0a8fcf512a7b48c88b3052d21f2eff1a <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N9202e2d866c1493b8a9151b5ee09a968 <http://www.cidoc-crm.org/cidoc-crm/P141_assigned> <https://id.rijksmuseum.nl/200140269> .
        _:Nd75a21fffb2f42cbaf123a3a8f6fa3de <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E54_Dimension> .
        _:N5492ef60c35c4f5d9f3bc23f6117c9ba <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E65_Creation> .
        _:N15d3ed5dcbf343539b6bafec92e4a3d6 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:Na1779b2ffa7f4b9989aa6b09c4e004d6 .
        _:N33c97a2c9c244f1c8177e12a8127ab8d <http://www.cidoc-crm.org/cidoc-crm/P177_assigned_property_of_type> <http://www.cidoc-crm.org/cidoc-crm/P15_was_influenced_by> .
        _:N7e3f01fdf4474b7c83fbc6c8e432231b <http://www.cidoc-crm.org/cidoc-crm/P141_assigned> <https://id.rijksmuseum.nl/200632800> .
        _:N3e08df9af24c40f58afdcff60e1f30be <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300456575> .
        _:Na7bfabc7e26645d4bf6702b2a89ebe38 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E54_Dimension> .
        _:N027a25da94e04bc0bd578b276c45ce92 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/22012> .
        _:N430e162d4f5e44f2a83395ebdaeb7eb6 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300445022> .
        _:Na2e28bbaa6ed4a4cab5c09738fd06bfa <http://www.cidoc-crm.org/cidoc-crm/P106i_forms_part_of> <https://id.rijksmuseum.nl/30166252> .
        _:N66ec8a07f33c40ffa762f4b20bbc836c <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300404670> .
        _:N5492ef60c35c4f5d9f3bc23f6117c9ba <http://www.cidoc-crm.org/cidoc-crm/P4_has_time-span> _:N7a8f1bd8a5734f2aaf0f1692e26b79e3 .
        <https://creativecommons.org/publicdomain/mark/1.0/> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E55_Type> .
        _:Nc21e4df26d3f4c409540c3d9882f7a2c <http://www.cidoc-crm.org/cidoc-crm/P91_has_unit> <http://vocab.getty.edu/aat/300379098> .
        _:N0e02d5ecb0d74c889cd09a38a989ef88 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435416> .
        _:N7e277d258b834c0f80be80cb95562238 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435416> .
        _:N608dde33f09f49f4817df74612a94b78 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N3bbcf21a24c742db8dc5f96f96589c3a .
        _:N326fcaa082c24b46b5f11d348e61775b <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388277> .
        _:N46369579875c4d4993a1e9115e4afd5c <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:Ne2e0a6cbff8242cf96b14a719ba4e236 .
        _:N9d83116074a84c1aba09f08548b4b6a6 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300456575> .
        _:Nb71fe9e9d62043b08a97bfea340fe166 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:Na2163ebe97c249608fda081dd3ab24a0 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        _:Nfebc8f394dae453391d1161bc0a9c8c0 <http://www.cidoc-crm.org/cidoc-crm/P106_is_composed_of> _:N081d86ce2eb84d278ef8fd2ef77bdf03 .
        <https://id.rijksmuseum.nl/202140269> <http://www.cidoc-crm.org/cidoc-crm/P104_is_subject_to> _:Nf4d33be5acfb487182a4cc317eac39f3 .
        _:N6627f4dbe3de4ae9892b257245e18310 <http://www.cidoc-crm.org/cidoc-crm/P177_assigned_property_of_type> <http://www.cidoc-crm.org/cidoc-crm/P15_was_influenced_by> .
        _:Nf5b24b74e0434c2294e883665c0d01f3 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "geheel" .
        _:N48d792fead8e4090a0ad284334194246 <http://www.cidoc-crm.org/cidoc-crm/P90_has_value> "20" .
        _:Nf12eee99ea474b61956284e5b4b3e03f <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "1" .
        _:N17e116ac376c41eeaa1884c0e5713ca5 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N3e08df9af24c40f58afdcff60e1f30be .
        _:Nb0899e1f3dcc40beaa1962cb3009fc91 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:N13bc57dedd8e4ef4914cdfbc2e826249 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388277> .
        _:N54379e36dc604eca9c327c7841436c2e <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N3fa85c9e0991441ead5f544faf65e1c9 .
        _:N64d5dc3e891a4d63abf4c0599b6b01e6 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:Nb33e6c41d95f4ecc964e87baf318bb30 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E13_Attribute_Assignment> .
        _:N7a8f1bd8a5734f2aaf0f1692e26b79e3 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:Nab29a88bd6624273b3e69f939bdc43d2 .
        _:Nc0730d8c31044cfb88248a7c618c1fe4 <http://www.cidoc-crm.org/cidoc-crm/P141_assigned> <https://id.rijksmuseum.nl/200140269> .
        _:Nf24b745418814730b2b21f19f5ab63ec <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N912e95b047ed4f699f1ff3e7076fd903 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "This wainscoting is from a house in Dordrecht. It is constructed according to the rules of Classical architecture, with columns surmounted by a frieze and a cornice. The marquetry in patterns of contrasting woods enlivens the wall. The continuous wainscoting created unity and lent distinction to an interior, as well as insulating it from the cold and damp." .
        _:N1cb7a3434e7c4805a84b96fd1cb75cba <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:Ne89c0c29dfa74d4dbb7770cc84a4304b .
        _:Nc0730d8c31044cfb88248a7c618c1fe4 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E13_Attribute_Assignment> .
        <https://creativecommons.org/publicdomain/zero/1.0/> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E55_Type> .
        _:Nbc6476862fc24fce8871a051a98d8932 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P43_has_dimension> _:N37947258001e4fe886ef5e16ee8d098b .
        _:Nb37f04e0249540e194ad05cd81fea8c6 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "wandsteen kolom" .
        _:N705c4d6a6699417995110eaab1c55117 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "geheel: hoogte 251 cm x breedte 840 cm (conform cat. 1952)" .
        _:N66ec8a07f33c40ffa762f4b20bbc836c <http://www.cidoc-crm.org/cidoc-crm/P106_is_composed_of> _:N70dd4554fd0445d5a0c1211e79eb5b53 .
        _:Nc2ab8d49b551404e9a60d49b2dca3862 <http://www.cidoc-crm.org/cidoc-crm/P91_has_unit> <http://vocab.getty.edu/aat/300379098> .
        _:N46e350cf3cb44e98a607d8f54ea4f04c <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        <https://id.rijksmuseum.nl/230171> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E53_Place> .
        _:Ne528a25442df400e9acea4aabf531466 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300004188> .
        _:N15d3ed5dcbf343539b6bafec92e4a3d6 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "length 189 cm" .
        <http://vocab.getty.edu/aat/300435429> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E55_Type> .
        _:N2b43b56170b14dd3914425a5e264d3c8 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:Nc4169ea2b4ce432794ea787e61e94c88 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        _:Naecfa816892c49c38a92d7eadfa75ae4 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:Nb7490660783349da8c8f3584b200fdb1 <http://www.cidoc-crm.org/cidoc-crm/P177_assigned_property_of_type> <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> .
        _:Nedd8d559277c461f9fe13fab7b26450b <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N6d361e0d732e413e80b8df766c403fcc <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E54_Dimension> .
        _:N59a34bd195db4121918f1827bdfbf755 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300260522> .
        _:Nd0da0cd3b0bf4e04833992add79cd921 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P43_has_dimension> _:N345d67f33b8443c9aef51ae71ff22990 .
        _:N3239b8eb4b284ff985aa2718a56b2f1e <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N175af0468c494b01bc82752ab8b10c39 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:N0ce70c349eb8403a8168e30af15c6b93 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:N7acecaf459d14b8ba111553f6a9673b0 <http://www.cidoc-crm.org/cidoc-crm/P90_has_value> "40" .
        _:Nc21e4df26d3f4c409540c3d9882f7a2c <http://www.cidoc-crm.org/cidoc-crm/P90_has_value> "30" .
        _:N10991c13ecad4042b6f74897010a2fd5 <http://www.cidoc-crm.org/cidoc-crm/P90_has_value> "115" .
        _:Nfbbd7c56a7e241ac8565ff0e8a1500d5 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:Nf1824cd4b39a41f5b5078f64bb063c43 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "1" .
        _:N1acc4d99a6674bdb9822837fc642ab16 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "1 x wandsteen kolom (rechthoekig), aan onderzijde gebroken" .
        <https://id.rijksmuseum.nl/2205125> <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:Ne5cbbc8733434408a0600147fede319b .
        _:Nf65276a3f25d4ade99a6af1dd57092ff <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300417268> .
        _:N2e450d51dde940b4960a72714bb2d9d9 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300311705> .
        <http://vocab.getty.edu/aat/300260522> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E55_Type> .
        _:Ncf59d64c146f4b54bdf1e2e0d57bfa66 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P43_has_dimension> _:N616b457f812f4e1696ba92dd99bc1989 .
        _:N9853680ebb9a422a914744450f06c61d <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "8" .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N082f41fa1877442bb605fceb4dab9da7 .
        _:N7992374a81c1459da0232a7f66bd5f94 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:Nfde69f83e1864cada3c4d42e90b0552d <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300312075> .
        _:N70dd4554fd0445d5a0c1211e79eb5b53 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300004188> .
        _:N58dff35c5ffd4a9699ff4d2f9812b5bc <http://www.cidoc-crm.org/cidoc-crm/P82a_begin_of_the_begin> "1877-01-01T00:00:00Z"^^<http://www.w3.org/2001/XMLSchema#dateTime> .
        _:Nb9b8092e98f84178b27a2308b5dea23e <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "plafond bedstee: lengte 189 cm (1 x plafondpaneel)" .
        _:N01be04987df14fdfbb1f874333ae213b <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:Nb71fe9e9d62043b08a97bfea340fe166 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N4c863561bde041fcacb50db185059c8a <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E54_Dimension> .
        _:Nc2ab8d49b551404e9a60d49b2dca3862 <http://www.cidoc-crm.org/cidoc-crm/P90_has_value> "173" .
        _:Nf5f0b55569a74f31a05f0096b42efe10 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:N985540f659474407a218059a2bc49b7d <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "pl. VII, afb. 18; pl. VIII, afb. 19, 21" .
        _:N54379e36dc604eca9c327c7841436c2e <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/22012> .
        _:N2b43b56170b14dd3914425a5e264d3c8 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300404670> .
        _:N082f41fa1877442bb605fceb4dab9da7 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:Ne5cbbc8733434408a0600147fede319b <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:Na7bfabc7e26645d4bf6702b2a89ebe38 <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:Nbc6476862fc24fce8871a051a98d8932 .
        _:Nd5d6fc8f1f5c4c25950b0592d4b78979 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "2018-02-27" .
        _:N2b43b56170b14dd3914425a5e264d3c8 <http://www.cidoc-crm.org/cidoc-crm/P106_is_composed_of> _:N88e0b897d1b2414f862c73f3ab315dff .
        _:Nb0899e1f3dcc40beaa1962cb3009fc91 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:Ndbb8fc769442469c89fcfafae4d956d3 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        _:N119d6c758d544f1894f6dd0f34450571 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N2fdf9d11a66045daafc63715d749a4e4 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:Nb0062b0bf6ad47fa9357e4598b8dc73f <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N9853680ebb9a422a914744450f06c61d .
        _:N64d5dc3e891a4d63abf4c0599b6b01e6 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:Ne6c70d7bc3994992a5e7cb760221e390 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:Nf1f87055185b4ede9449784a331c65c4 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "Th. H. Lunsingh Scheurleer, 'Vroeg XVIIe-eeuwse Dordtse betimmeringen', Bulletin van het Koninklijk Nederlands Oudheidkundige Bond 1952." .
        _:N8c181583a636475f93830394d629094c <http://www.cidoc-crm.org/cidoc-crm/P106_is_composed_of> _:Nd295802bf45949a99e46328665a91c1c .
        _:N71f9d7c8591b43fea200c2f20153243e <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "14" .
        _:N66ec8a07f33c40ffa762f4b20bbc836c <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:N48d792fead8e4090a0ad284334194246 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N3e639b13c720410785ae09160f0d8dd4 .
        _:N8fcde2458f8a46b19fd7ebc5dbd66191 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "9" .
        _:N54379e36dc604eca9c327c7841436c2e <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N46e350cf3cb44e98a607d8f54ea4f04c .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/2202602> .
        _:Naee0553c2b924efda8b2f48af18f3d93 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E52_Time-Span> .
        _:N2e450d51dde940b4960a72714bb2d9d9 <http://www.cidoc-crm.org/cidoc-crm/P106_is_composed_of> _:N985540f659474407a218059a2bc49b7d .
        _:Na5f8e89eb41442b2a53885a6630913b7 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N2ac9912314b0440abca8ea7ad2d0b40f <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:Nc2ab8d49b551404e9a60d49b2dca3862 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N372342e34bde4672836392b9ea4bcfac .
        _:Nf57ec8fb8c364c9dad7c26971e3e956a <http://www.cidoc-crm.org/cidoc-crm/P106_is_composed_of> _:N834d394a4d8140769b70024caf6d3850 .
        _:N5dd0d1de24294ec5a2b1f9b4c025be51 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        _:N027a25da94e04bc0bd578b276c45ce92 <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:Nb82f1f80a4d346b99f2a8fb69c43ca29 .
        _:N46369579875c4d4993a1e9115e4afd5c <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:Nbe7f9e24a4044ddba9a04c8af14b8cb8 .
        _:N7a5d1eaef1a044429136dad2a15c9fac <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388277> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N3c1023bca87d4df3afb4a17c87a21236 .
        _:N0ce70c349eb8403a8168e30af15c6b93 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "kolom schouw" .
        _:N9f04257021c844ad9f03d1cf48540509 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N1caa6709b1554c4dbf1ef2a03c7a74fd .
        _:Nbeff3cf5db1548de8f0c6a6b424fe4bb <http://www.cidoc-crm.org/cidoc-crm/P141_assigned> _:N81413029a74e471d884349daca1067ce .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P129i_is_subject_of> _:Nf65276a3f25d4ade99a6af1dd57092ff .
        _:N187de5db104b498285561e41ac556499 <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N658aff6bbc4d45db8b4b42450712f00e .
        _:Nf4d33be5acfb487182a4cc317eac39f3 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://creativecommons.org/publicdomain/mark/1.0/> .
        _:N71f9d7c8591b43fea200c2f20153243e <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:Nb412bc5b75614a6b9f89b97a4c6b71e1 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:N5d89ec6c9e8e4da5ae945adc33afe621 <http://www.cidoc-crm.org/cidoc-crm/P90_has_value> "5" .
        _:Nf1f87055185b4ede9449784a331c65c4 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300311705> .
        _:N10991c13ecad4042b6f74897010a2fd5 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N6ec0951cf9844dd6840ed80331795ac6 .
        _:N5d89ec6c9e8e4da5ae945adc33afe621 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N3e185a0c0020413da970158c34c0d4cd .
        _:N58dff35c5ffd4a9699ff4d2f9812b5bc <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N2d5a5881f1f844a9949c76113b67c0d7 .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P43_has_dimension> _:N3b8054b7b5944f5483da63d105d116ac .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P141i_was_assigned_by> _:N6b4b28e0287741169a5e817405736a78 .
        _:N1ac61619e0104c48bc0939096b9d3d98 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "3" .
        _:Na5f8e89eb41442b2a53885a6630913b7 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388277> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:Naecfa816892c49c38a92d7eadfa75ae4 .
        <https://id.rijksmuseum.nl/220400> <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N18477e1a18684649b862535722c3366b .
        _:N09ddaca824f34874be53c19746261aaa <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N66ec8a07f33c40ffa762f4b20bbc836c <http://www.cidoc-crm.org/cidoc-crm/P106_is_composed_of> _:N0cd9a3d62b8a4d2eb55832a64919dfdd .
        _:N027a25da94e04bc0bd578b276c45ce92 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E54_Dimension> .
        _:Nfd49546aacb1470594f93824a9041c17 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N6d361e0d732e413e80b8df766c403fcc <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N0a8fcf512a7b48c88b3052d21f2eff1a .
        _:N7987dfeff72a4a079682b0fc0ef2adcc <http://www.cidoc-crm.org/cidoc-crm/P91_has_unit> <http://vocab.getty.edu/aat/300379098> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N1b3ed30ab1d848b183ae623b1b6f73e8 .
        <https://id.rijksmuseum.nl/202140269> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E36_Visual_Item> .
        _:Nb82f1f80a4d346b99f2a8fb69c43ca29 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N09412cb461ed4f19bb7390358576be19 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N80a9d20c250c4bf98625378781048e22 <http://www.cidoc-crm.org/cidoc-crm/P91_has_unit> <http://vocab.getty.edu/aat/300379098> .
        _:N2bcf69baf4334e1bb1ebfba3e5a96afc <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N541427f2d233458e9bc8084d00f36fc3 .
        _:Nb7a53c8fd8d7436094345a156e356e39 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E54_Dimension> .
        _:N33730449371c4173a22a9814bef22a21 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/2201366> .
        _:N0e02d5ecb0d74c889cd09a38a989ef88 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:Nb9d8d388a0d740bc883fa0ef3581de24 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        _:Nf5f0b55569a74f31a05f0096b42efe10 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:Nd5c88d41417c4995bebbfefe3e23aa3f <http://www.cidoc-crm.org/cidoc-crm/P141_assigned> <https://id.rijksmuseum.nl/200140269> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N0880a231761441dcbb57606e8decb557 .
        _:Nd888db644e0341279e46077c24364912 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:Ncd301494c82849caba4115a0d298fade <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N1a0866183b184f5bbdec3e1b3c980274 .
        _:N3b2a98dbac624848ac3dd47af776626b <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E13_Attribute_Assignment> .
        _:N4c863561bde041fcacb50db185059c8a <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N0aa35f5814a04ddc8992ec1a23c87509 .
        _:Nb44a375aa47a499e9387bf65d1bd0f8c <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:N7f966aa3fc8f4ceaac4955a7996452b4 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N054da200073441e0adbbdd9d84fc4568 <http://www.cidoc-crm.org/cidoc-crm/P91_has_unit> <http://vocab.getty.edu/aat/300379098> .
        _:N5452c79ad18548d59c42e3844d13a003 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/22012> .
        _:N94263c52765547b0b208b79cfa7824b2 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E13_Attribute_Assignment> .
        _:N7c21cb705a4749f28e6b286c592abd92 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        _:Nd0da0cd3b0bf4e04833992add79cd921 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:N175af0468c494b01bc82752ab8b10c39 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        <http://vocab.getty.edu/aat/300445022> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E55_Type> .
        _:N0cd9a3d62b8a4d2eb55832a64919dfdd <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388277> .
        _:N0585088e0a45457485e54372541fb56a <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:Na19ab59d113f41189b70ab80b863ef3f .
        _:Nd75a21fffb2f42cbaf123a3a8f6fa3de <http://www.cidoc-crm.org/cidoc-crm/P90_has_value> "176" .
        _:N175af0468c494b01bc82752ab8b10c39 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "geheel" .
        _:N0cd9a3d62b8a4d2eb55832a64919dfdd <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300260522> .
        _:N834d394a4d8140769b70024caf6d3850 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "14" .
        _:N28dd45fcc8034fce905c95d208d82ee5 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        _:N541427f2d233458e9bc8084d00f36fc3 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N187de5db104b498285561e41ac556499 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E54_Dimension> .
        _:N5371ecd19a6b4420b5b0b818c39dc033 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300312075> .
        _:Nca4369bc9b714f04b162701fa9ebb6c0 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/2203> .
        _:N4c863561bde041fcacb50db185059c8a <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/22011> .
        _:N7b763e33a1fe4a919a458f76bcffaee4 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "1" .
        _:N13bc57dedd8e4ef4914cdfbc2e826249 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:Nb82f1f80a4d346b99f2a8fb69c43ca29 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        _:N483c3aa94f0f4140a3d8c360a284840e <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:Ne03ff39fbb0c40e28a029d5f7d29dcd3 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:N9e29bd1609c242668d0b27932fcfea8d <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300311705> .
        _:N09318b67d7404c08bd1417dcd50778f2 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:Nfebc8f394dae453391d1161bc0a9c8c0 .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P43_has_dimension> _:N0585088e0a45457485e54372541fb56a .
        _:N09f93d0f42bc47a48d8f98adf5aa17ab <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:Nb33e6c41d95f4ecc964e87baf318bb30 <http://www.cidoc-crm.org/cidoc-crm/P177_assigned_property_of_type> <http://www.cidoc-crm.org/cidoc-crm/P15_was_influenced_by> .
        <https://id.rijksmuseum.nl/26139> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://linked.art/ns/terms/Set> .
        _:Ncf3c779254b84e9fb3da285617b4e7e7 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N8b8fe726baa048e484b6f096eb04b8c2 .
        _:N95bcf74bfc184ed09817d8587821b356 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        _:Ncd301494c82849caba4115a0d298fade <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E54_Dimension> .
        _:N0880a231761441dcbb57606e8decb557 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "zijwand bedstee: lengte 176 cm (1 x wandpaneel)" .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:Nb9b8092e98f84178b27a2308b5dea23e .
        _:N81413029a74e471d884349daca1067ce <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:Na2a8b3c2453e4826b1f8b1ac821736ab .
        _:N326aae03a4974a92953f4f3132f7c866 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388277> .
        _:Ndc9392ef2fd84fd78a5ab569d96a9b8c <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:Ne6fb6c600d3e4db5ba6325f7d36203b6 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300404450> .
        _:Ne1f2017392124d449f1d5c2b65ed01c2 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "0 (De onderstaande maten zijn de maten van DE GEHELE BETIMMERING. De maten zijn afkomstig uit de documentatie van Aannemingbedrijf J.Kneppers, van offerte/werkvoorstel met werknummer 04/085. Gemaakt tijdens de verhuizing 2003.)" .
        _:Naee0553c2b924efda8b2f48af18f3d93 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N601e00fa88834f91ba480248515ee765 .
        _:Nf68b0b2a16044b53901390eed14c6ad3 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:Nb606016b3c3a43668276a89000e202fc <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300456575> .
        _:Nd75a21fffb2f42cbaf123a3a8f6fa3de <http://www.cidoc-crm.org/cidoc-crm/P91_has_unit> <http://vocab.getty.edu/aat/300379098> .
        <https://data.rijksmuseum.nl/200140269> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N1a0866183b184f5bbdec3e1b3c980274 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N0880a231761441dcbb57606e8decb557 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:N068d3af813a84822a9a10252e1f90654 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "anoniem" .
        _:Nff57fa74386646cf99bd1a83860f45af <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388277> .
        _:N1f3bcdeb3f524aa996b98fc3dce46a9c <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:N187de5db104b498285561e41ac556499 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N3859a270ab8a4f8380f03ab1c0bbccc7 .
        <https://id.rijksmuseum.nl/220147> <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N8fcde2458f8a46b19fd7ebc5dbd66191 .
        _:Nf004dd8e9ac64490b4f1d9f3f1009b2f <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:N2d00c5101f844d34acd31d2b253a4282 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388277> .
        _:Na983800a88d945a5a51a6fe0491c3878 <http://www.cidoc-crm.org/cidoc-crm/P141_assigned> <https://id.rijksmuseum.nl/200140269> .
        _:Necea879225e24b18affc4d99504cb152 <http://www.cidoc-crm.org/cidoc-crm/P141i_was_assigned_by> _:N3b2a98dbac624848ac3dd47af776626b .
        _:N82590e8f23af4251a37c031c32f125dc <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/2203> .
        _:N6b20b0bc4ce8442f87e5e14187a5e606 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "Dordrecht, 1626, diverse houtsoorten" .
        _:N2ced60f46cdd4ab3a6f14354d9fd817d <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N6d361e0d732e413e80b8df766c403fcc <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N28dd45fcc8034fce905c95d208d82ee5 .
        _:N22aa8fbc2b2e47b9b9fea725fad48065 <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:Na5e61396949640109227da3a437d15fe .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P43_has_dimension> _:Nd91c97946f9544deba324bdfa2acf583 .
        _:N0e02d5ecb0d74c889cd09a38a989ef88 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:Nb0062b0bf6ad47fa9357e4598b8dc73f <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        <https://id.rijksmuseum.nl/2202602> <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435443> .
        _:N722102f196cd4dd089bc5bf9a40257ca <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N912e95b047ed4f699f1ff3e7076fd903 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300048722> .
        _:N7e277d258b834c0f80be80cb95562238 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "anoniem, anonymous, anonymous, anoniem" .
        _:N8fcde2458f8a46b19fd7ebc5dbd66191 <http://www.cidoc-crm.org/cidoc-crm/P141i_was_assigned_by> _:Nf7dbe80f8d4b46d680024f9ab39b50e6 .
        _:Nb44a375aa47a499e9387bf65d1bd0f8c <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:Nfcb44b36ba5f4e2e95f6ce192f5e1da6 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:Ne359204a393a4afeaeb69ed89ea83ded <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300456575> .
        _:N1b3ed30ab1d848b183ae623b1b6f73e8 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "height 250 cm" .
        _:Nb9b8092e98f84178b27a2308b5dea23e <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N3859a270ab8a4f8380f03ab1c0bbccc7 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        _:N54379e36dc604eca9c327c7841436c2e <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E54_Dimension> .
        _:Nbe7f9e24a4044ddba9a04c8af14b8cb8 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:Ncfac004fcdc044ff9bd05a4f96a5d6cd <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "vervaardiger: anoniem, Dordrecht" .
        _:N834d394a4d8140769b70024caf6d3850 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        <http://vocab.getty.edu/aat/300435443> <http://www.w3.org/2000/01/rdf-schema#label> "Type of Work" .
        _:N13bc57dedd8e4ef4914cdfbc2e826249 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "height 40 cm x height 40 cm" .
        _:N054da200073441e0adbbdd9d84fc4568 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E54_Dimension> .
        _:N345d67f33b8443c9aef51ae71ff22990 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:Nb71fe9e9d62043b08a97bfea340fe166 .
        _:N68dee9dbffc4437d8539b0964f13a7eb <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:Nb606016b3c3a43668276a89000e202fc .
        _:N10a54ac58ff24ee0ad919ee913a09098 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E13_Attribute_Assignment> .
        _:Nf24b745418814730b2b21f19f5ab63ec <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:Nb606016b3c3a43668276a89000e202fc <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "11" .
        _:Ne03ff39fbb0c40e28a029d5f7d29dcd3 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:Nff57fa74386646cf99bd1a83860f45af .
        _:N103d06b66ba34d26bc4071edd23a3385 <http://www.cidoc-crm.org/cidoc-crm/P141_assigned> <https://id.rijksmuseum.nl/200140269> .
        <https://id.rijksmuseum.nl/2202602> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E55_Type> .
        _:N722102f196cd4dd089bc5bf9a40257ca <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N4841974218ed4f44b01113de5a960a2a <http://www.cidoc-crm.org/cidoc-crm/P91_has_unit> <http://vocab.getty.edu/aat/300379098> .
        _:N4c863561bde041fcacb50db185059c8a <http://www.cidoc-crm.org/cidoc-crm/P91_has_unit> <http://vocab.getty.edu/aat/300379098> .
        _:N345d67f33b8443c9aef51ae71ff22990 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E54_Dimension> .
        <http://vocab.getty.edu/aat/300388277> <http://www.w3.org/2000/01/rdf-schema#label> "English" .
        _:N0cb07388ba2a4f8c8344bfb6e024f3bc <http://www.cidoc-crm.org/cidoc-crm/P90_has_value> "98" .
        _:N6b4b28e0287741169a5e817405736a78 <http://www.cidoc-crm.org/cidoc-crm/P141_assigned> _:N2199894fb15e4d7e82b807925e431e62 .
        _:N5452c79ad18548d59c42e3844d13a003 <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:Ndbb8fc769442469c89fcfafae4d956d3 .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N09ddaca824f34874be53c19746261aaa .
        _:Nf0260e9707094511901daf9ab473565a <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:Nce8be56f772b4597a87c3c8886178f39 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:Nd75a21fffb2f42cbaf123a3a8f6fa3de <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N0cab1d0fb97a4a58a25c186a712a3276 .
        _:Naecfa816892c49c38a92d7eadfa75ae4 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:Nf1f87055185b4ede9449784a331c65c4 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:N1a462cc9f2b142a3ad30e821b9193592 <http://www.cidoc-crm.org/cidoc-crm/P90_has_value> "60" .
        _:N4ea6864a30394ca09e8e1f8ef3a51a53 <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N2ced60f46cdd4ab3a6f14354d9fd817d .
        _:N3b8054b7b5944f5483da63d105d116ac <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N7c21cb705a4749f28e6b286c592abd92 .
        _:Nc21e4df26d3f4c409540c3d9882f7a2c <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:Nb7476f387a964cc885ceba968cdf3f6a .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N64d5dc3e891a4d63abf4c0599b6b01e6 .
        <http://vocab.getty.edu/aat/300379391> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E55_Type> .
        _:N7f966aa3fc8f4ceaac4955a7996452b4 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "1 x wandpaneel (2 stukjes hout paneel los)" .
        _:N68dee9dbffc4437d8539b0964f13a7eb <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:Nfebc8f394dae453391d1161bc0a9c8c0 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435449> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/2202215> .
        _:N9f04257021c844ad9f03d1cf48540509 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E13_Attribute_Assignment> .
        _:N885109c17a1840c8bc48ebc3a6426581 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300456575> .
        _:N6ec0951cf9844dd6840ed80331795ac6 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "wandsteen kolom" .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P43_has_dimension> _:Naad832a2d3574eb9934e19146aaf96df .
        _:N053403eb2d9e45f99f1da036db71b1ee <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N01be04987df14fdfbb1f874333ae213b <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388277> .
        _:N22aa8fbc2b2e47b9b9fea725fad48065 <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N7e277d258b834c0f80be80cb95562238 .
        _:N6deccae762f543ff8edc6d030cf85cb1 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E54_Dimension> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P43_has_dimension> _:N1a462cc9f2b142a3ad30e821b9193592 .
        _:Ne528a25442df400e9acea4aabf531466 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:N1caa6709b1554c4dbf1ef2a03c7a74fd <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:Nca4369bc9b714f04b162701fa9ebb6c0 <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:Nf24b745418814730b2b21f19f5ab63ec .
        <https://id.rijksmuseum.nl/220400> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E57_Material> .
        _:N17e116ac376c41eeaa1884c0e5713ca5 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P43_has_dimension> _:Nb542bdb6c71c4f2d8e69c260634d9d07 .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P43_has_dimension> _:N6b0dee5761c544e7bdca4844a780cac1 .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P45_consists_of> <https://id.rijksmuseum.nl/220147> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P43_has_dimension> _:Nca4369bc9b714f04b162701fa9ebb6c0 .
        _:Na1779b2ffa7f4b9989aa6b09c4e004d6 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:N119d6c758d544f1894f6dd0f34450571 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "maker: anonymous, Dordrecht" .
        _:Nbd32e6417f644bc4bbe678599a84d9a1 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        _:Nb0899e1f3dcc40beaa1962cb3009fc91 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N27a101c38ecc45a2a456bfb43524f36e <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435452> .
        _:N3e185a0c0020413da970158c34c0d4cd <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:N64d5dc3e891a4d63abf4c0599b6b01e6 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N2199894fb15e4d7e82b807925e431e62 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N1c6a400b9d1c4264953b51c48725e82a <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "p. 56, afb. 12" .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P43_has_dimension> _:N0cb07388ba2a4f8c8344bfb6e024f3bc .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P43_has_dimension> _:Nc2ab8d49b551404e9a60d49b2dca3862 .
        _:N5d861f12afca43e9879bd7bab9b16288 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388277> .
        _:Ncfac004fcdc044ff9bd05a4f96a5d6cd <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        <https://id.rijksmuseum.nl/220432> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E55_Type> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P43_has_dimension> _:N82590e8f23af4251a37c031c32f125dc .
        _:Nb7a53c8fd8d7436094345a156e356e39 <http://www.cidoc-crm.org/cidoc-crm/P90_has_value> "20" .
        _:Nb7a53c8fd8d7436094345a156e356e39 <http://www.cidoc-crm.org/cidoc-crm/P91_has_unit> <http://vocab.getty.edu/aat/300379098> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P43_has_dimension> _:Nc21e4df26d3f4c409540c3d9882f7a2c .
        _:N3f0071080f814903b65c8093e0b87567 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "wandpaneel" .
        _:N70dd4554fd0445d5a0c1211e79eb5b53 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:N0aa35f5814a04ddc8992ec1a23c87509 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:N4841974218ed4f44b01113de5a960a2a <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E54_Dimension> .
        _:Nfbbd7c56a7e241ac8565ff0e8a1500d5 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:Ne359204a393a4afeaeb69ed89ea83ded .
        _:N48d792fead8e4090a0ad284334194246 <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N722102f196cd4dd089bc5bf9a40257ca .
        _:N1a6332eb389645caa5a17dde503440be <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:Na2302e47b8ba46bbba23d0f8ff03a902 .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N68dee9dbffc4437d8539b0964f13a7eb .
        _:Na7bfabc7e26645d4bf6702b2a89ebe38 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:Nf0260e9707094511901daf9ab473565a .
        _:Ne5cbbc8733434408a0600147fede319b <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300456575> .
        _:N22aa8fbc2b2e47b9b9fea725fad48065 <http://www.cidoc-crm.org/cidoc-crm/P32_used_general_technique> <https://id.rijksmuseum.nl/2202604> .
        _:N0585088e0a45457485e54372541fb56a <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/22012> .
        _:N45abc2b7fbd144e98e4caca8ea712536 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300456575> .
        _:Na467b5ec285348b9a5549ba677c13dba <http://www.cidoc-crm.org/cidoc-crm/P177_assigned_property_of_type> <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> .
        _:Ncfac004fcdc044ff9bd05a4f96a5d6cd <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N187de5db104b498285561e41ac556499 <http://www.cidoc-crm.org/cidoc-crm/P91_has_unit> <http://vocab.getty.edu/aat/300379098> .
        _:N09318b67d7404c08bd1417dcd50778f2 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E53_Place> .
        <http://vocab.getty.edu/aat/300404670> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E55_Type> .
        _:N2d5a5881f1f844a9949c76113b67c0d7 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:Nfbbd7c56a7e241ac8565ff0e8a1500d5 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N45abc2b7fbd144e98e4caca8ea712536 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "14" .
        <http://vocab.getty.edu/aat/300435430> <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300418049> .
        _:Nb412bc5b75614a6b9f89b97a4c6b71e1 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "17de Eeuw" .
        _:N46369579875c4d4993a1e9115e4afd5c <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/22012> .
        _:N10a54ac58ff24ee0ad919ee913a09098 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:Nf1824cd4b39a41f5b5078f64bb063c43 .
        _:Nff57fa74386646cf99bd1a83860f45af <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P45_consists_of> <https://id.rijksmuseum.nl/220149> .
        _:N9f7bfe219f334214a1fa69b1f708806a <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N67eab31835754e12837562bab5f500a0 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:Nf508696bbaf14889b6996a0620cf4805 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "7" .
        _:Nf3e78ce4061f4ba4bc87ece8120be08a <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        <https://id.rijksmuseum.nl/2201366> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E55_Type> .
        _:N7b763e33a1fe4a919a458f76bcffaee4 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:N18477e1a18684649b862535722c3366b <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300456575> .
        _:N6c6d3829ad7b40f4b98b8e3f2661b011 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N71f9d7c8591b43fea200c2f20153243e <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300456575> .
        _:N4bec33370efd46e8a61e1adb740013a9 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:N6deccae762f543ff8edc6d030cf85cb1 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:Nd888db644e0341279e46077c24364912 .
        _:N37947258001e4fe886ef5e16ee8d098b <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N82cc48ea181f4b719a5df1a66123dc02 .
        _:N81413029a74e471d884349daca1067ce <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N971952f14ca64c16877973270227af01 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:N705c4d6a6699417995110eaab1c55117 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N67eab31835754e12837562bab5f500a0 .
        _:N7ac2ff624a324d1d84f7a33274977e50 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "p. 117-119, afb. 28, 30" .
        _:N7f966aa3fc8f4ceaac4955a7996452b4 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:N7e3f01fdf4474b7c83fbc6c8e432231b <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N3679ab9f033b4a508bfcf0c4414ff0a8 .
        _:Nd295802bf45949a99e46328665a91c1c <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "14" .
        _:N2bcf69baf4334e1bb1ebfba3e5a96afc <http://www.cidoc-crm.org/cidoc-crm/P90_has_value> "132.5" .
        _:N82590e8f23af4251a37c031c32f125dc <http://www.cidoc-crm.org/cidoc-crm/P90_has_value> "15" .
        _:N22aa8fbc2b2e47b9b9fea725fad48065 <http://www.cidoc-crm.org/cidoc-crm/P4_has_time-span> _:Naee0553c2b924efda8b2f48af18f3d93 .
        _:Ne1f77dcd13b94e0cacaa3f647ca7d58d <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N7987dfeff72a4a079682b0fc0ef2adcc <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/22026> .
        <https://id.rijksmuseum.nl/2201452> <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:Necea879225e24b18affc4d99504cb152 .
        _:N62373814cc20414594e8e2d863115be4 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        _:N9d83116074a84c1aba09f08548b4b6a6 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "11" .
        _:Na5f8e89eb41442b2a53885a6630913b7 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435417> .
        _:N7987dfeff72a4a079682b0fc0ef2adcc <http://www.cidoc-crm.org/cidoc-crm/P90_has_value> "189" .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P43_has_dimension> _:N54379e36dc604eca9c327c7841436c2e .
        _:N5151ca6daaeb4a48ac8c1a44279166a6 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:Naad832a2d3574eb9934e19146aaf96df <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E54_Dimension> .
        _:Nb7476f387a964cc885ceba968cdf3f6a <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        _:N541427f2d233458e9bc8084d00f36fc3 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:N24a73ce7bd9b49c6ba1155d2578dac6a <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:N4c863561bde041fcacb50db185059c8a <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N3f0071080f814903b65c8093e0b87567 .
        _:N3e639b13c720410785ae09160f0d8dd4 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:Nf004dd8e9ac64490b4f1d9f3f1009b2f <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "6" .
        <http://vocab.getty.edu/aat/300404450> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E55_Type> .
        _:N35e44becd20b419593d5ff5efe283bd0 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N0aa35f5814a04ddc8992ec1a23c87509 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:Nbafe8ea81b65469598b2bc9eea31891e <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:Ncd301494c82849caba4115a0d298fade <http://www.cidoc-crm.org/cidoc-crm/P91_has_unit> <http://vocab.getty.edu/aat/300379098> .
        _:N595302ef02574bce97929841aea079fb <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:Nc4ddfca1ccc14e5eb07dd27528790a0d <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:Ne89c0c29dfa74d4dbb7770cc84a4304b <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        <https://id.rijksmuseum.nl/2202604> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E55_Type> .
        _:N1d8689097c9f4d91b58fc616df41dd2d <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://creativecommons.org/publicdomain/zero/1.0/> .
        _:Nd8b124c87b204e2ea53d3fbfb970ed65 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E8_Acquisition> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N27a101c38ecc45a2a456bfb43524f36e .
        _:Ne6fb6c600d3e4db5ba6325f7d36203b6 <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N119d6c758d544f1894f6dd0f34450571 .
        _:Ne1f2017392124d449f1d5c2b65ed01c2 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N33730449371c4173a22a9814bef22a21 .
        _:N0585088e0a45457485e54372541fb56a <http://www.cidoc-crm.org/cidoc-crm/P91_has_unit> <http://vocab.getty.edu/aat/300379098> .
        _:N27a101c38ecc45a2a456bfb43524f36e <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N616b457f812f4e1696ba92dd99bc1989 <http://www.cidoc-crm.org/cidoc-crm/P91_has_unit> <http://vocab.getty.edu/aat/300379098> .
        _:Nbeff3cf5db1548de8f0c6a6b424fe4bb <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300311954> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P43_has_dimension> _:N4841974218ed4f44b01113de5a960a2a .
        <https://id.rijksmuseum.nl/242140269> <http://www.cidoc-crm.org/cidoc-crm/P9_consists_of> _:Nd8b124c87b204e2ea53d3fbfb970ed65 .
        <https://id.rijksmuseum.nl/200140262> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E22_Human-Made_Object> .
        _:Nb542bdb6c71c4f2d8e69c260634d9d07 <http://www.cidoc-crm.org/cidoc-crm/P90_has_value> "115" .
        _:N0cab1d0fb97a4a58a25c186a712a3276 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N3fa85c9e0991441ead5f544faf65e1c9 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:N70dd4554fd0445d5a0c1211e79eb5b53 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "Main building" .
        _:N4ea6864a30394ca09e8e1f8ef3a51a53 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:Nfd49546aacb1470594f93824a9041c17 .
        _:N5371ecd19a6b4420b5b0b818c39dc033 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N345d67f33b8443c9aef51ae71ff22990 <http://www.cidoc-crm.org/cidoc-crm/P91_has_unit> <http://vocab.getty.edu/aat/300379098> .
        _:N8c181583a636475f93830394d629094c <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300311705> .
        _:N80a9d20c250c4bf98625378781048e22 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/2203> .
        _:N6c6d3829ad7b40f4b98b8e3f2661b011 <http://www.cidoc-crm.org/cidoc-crm/P106_is_composed_of> _:N3ad1d58543eb469d8f0644d22387f287 .
        _:Nd295802bf45949a99e46328665a91c1c <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300404620> .
        _:N053403eb2d9e45f99f1da036db71b1ee <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:Ne6c70d7bc3994992a5e7cb760221e390 .
        _:N10a54ac58ff24ee0ad919ee913a09098 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300311954> .
        _:Nd91c97946f9544deba324bdfa2acf583 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E54_Dimension> .
        _:N2ced60f46cdd4ab3a6f14354d9fd817d <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N1ea15331a2a04f61a9e7f549ffe9b8e3 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300456575> .
        <https://id.rijksmuseum.nl/2203658> <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N3c674b37f0574fc19bf820b10b42d812 .
        _:N4ea6864a30394ca09e8e1f8ef3a51a53 <http://www.cidoc-crm.org/cidoc-crm/P90_has_value> "250" .
        _:N0cb07388ba2a4f8c8344bfb6e024f3bc <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E54_Dimension> .
        _:Na5f8e89eb41442b2a53885a6630913b7 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "anonymous" .
        _:Nd75a21fffb2f42cbaf123a3a8f6fa3de <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/22026> .
        _:N58dff35c5ffd4a9699ff4d2f9812b5bc <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:Nbd1e5854266f4be8971af77ce121fe39 .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N17e116ac376c41eeaa1884c0e5713ca5 .
        _:N5c16dbaa70544c5ca1e482f85099cefc <http://www.cidoc-crm.org/cidoc-crm/P106_is_composed_of> _:N482dd2adec334db989fce4e1be63fe68 .
        _:Necea879225e24b18affc4d99504cb152 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300456575> .
        _:Nb0062b0bf6ad47fa9357e4598b8dc73f <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:Nc5f8aa4aa4714fddadb069e47a3f3e8f <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "maker: anoniem, Dordrecht" .
        _:N7e277d258b834c0f80be80cb95562238 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N27a101c38ecc45a2a456bfb43524f36e <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N54379e36dc604eca9c327c7841436c2e <http://www.cidoc-crm.org/cidoc-crm/P91_has_unit> <http://vocab.getty.edu/aat/300379098> .
        _:N7e3f01fdf4474b7c83fbc6c8e432231b <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E13_Attribute_Assignment> .
        _:N3c674b37f0574fc19bf820b10b42d812 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "8" .
        _:N6b4b28e0287741169a5e817405736a78 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300311954> .
        <https://id.rijksmuseum.nl/22011> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E55_Type> .
        _:N37f56317157d4e5292e352fbf1c81916 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388277> .
        _:Nc02025eb8dac4dce94feba87e938d55c <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300456575> .
        _:Na467b5ec285348b9a5549ba677c13dba <http://www.cidoc-crm.org/cidoc-crm/P141_assigned> _:N7992374a81c1459da0232a7f66bd5f94 .
        <https://id.rijksmuseum.nl/2205125> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E57_Material> .
        _:N94263c52765547b0b208b79cfa7824b2 <http://www.cidoc-crm.org/cidoc-crm/P141_assigned> _:Na4ed40dc21804706b623189d751b6fd1 .
        _:Na9cacc1829df47ecb369f81d1bc11693 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:Nccfaeb94540c4421ab4975acb489d11f <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:N68dee9dbffc4437d8539b0964f13a7eb <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "console schouw: hoogte 40 cm (1 x console (zit op kolom)) x hoogte 40 cm (1 x console (zit op kolom))" .
        _:N345d67f33b8443c9aef51ae71ff22990 <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:Nb44a375aa47a499e9387bf65d1bd0f8c .
        _:N67eab31835754e12837562bab5f500a0 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "1" .
        _:N80a9d20c250c4bf98625378781048e22 <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N483c3aa94f0f4140a3d8c360a284840e .
        _:Nf004dd8e9ac64490b4f1d9f3f1009b2f <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300456575> .
        _:Nbd32e6417f644bc4bbe678599a84d9a1 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        <https://id.rijksmuseum.nl/22015> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E55_Type> .
        _:N6f6d1d215da54c718f7bcbf200bdeb70 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:Nc9bb1c958c024f86bed9da3b7c8724fd .
        <http://vocab.getty.edu/aat/300435452> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E55_Type> .
        _:N13bc57dedd8e4ef4914cdfbc2e826249 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        <https://id.rijksmuseum.nl/2203658> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E57_Material> .
        _:Nb7476f387a964cc885ceba968cdf3f6a <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:N595302ef02574bce97929841aea079fb <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        <https://id.rijksmuseum.nl/22015> <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435443> .
        _:N8b8fe726baa048e484b6f096eb04b8c2 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:Ne89c0c29dfa74d4dbb7770cc84a4304b <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N5c16dbaa70544c5ca1e482f85099cefc <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300311705> .
        _:Nb4b2aae9d771492b84fefc048c75ce40 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:Naad832a2d3574eb9934e19146aaf96df <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N439a7b29c632470987ba69c53f6ea05a .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P141i_was_assigned_by> _:Nbeff3cf5db1548de8f0c6a6b424fe4bb .
        _:N6deccae762f543ff8edc6d030cf85cb1 <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N7f79f5380ec84a009fb337efe323e347 .
        _:N5a1cb55c4e164ddca0ebb0b8f6d0a743 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:N027a25da94e04bc0bd578b276c45ce92 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:Nbafe8ea81b65469598b2bc9eea31891e .
        _:N068d3af813a84822a9a10252e1f90654 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N082f41fa1877442bb605fceb4dab9da7 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N9fac90d69ab74000b3ec6ce5db36a70c .
        _:Nbe7f9e24a4044ddba9a04c8af14b8cb8 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:Nc2555581e07b470f9ae3c85d2c5bc75f <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N68dee9dbffc4437d8539b0964f13a7eb <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N7992374a81c1459da0232a7f66bd5f94 <http://www.cidoc-crm.org/cidoc-crm/P106i_forms_part_of> <https://id.rijksmuseum.nl/301151248> .
        _:N11eedb37d5ea4da598e5e788962d483b <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:Ne2e0a6cbff8242cf96b14a719ba4e236 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N5d89ec6c9e8e4da5ae945adc33afe621 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E54_Dimension> .
        _:N7c1ab7ef63274e8b87a71f557ad956b8 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N0bd6f8641bfd4752ae8f824aff7758fe <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P43_has_dimension> _:N80a9d20c250c4bf98625378781048e22 .
        _:N2e450d51dde940b4960a72714bb2d9d9 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        <http://vocab.getty.edu/aat/300311954> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E55_Type> .
        _:N6d361e0d732e413e80b8df766c403fcc <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/2203> .
        _:N6deccae762f543ff8edc6d030cf85cb1 <http://www.cidoc-crm.org/cidoc-crm/P91_has_unit> <http://vocab.getty.edu/aat/300379098> .
        _:N15d3ed5dcbf343539b6bafec92e4a3d6 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388277> .
        _:N46369579875c4d4993a1e9115e4afd5c <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E54_Dimension> .
        _:Na2302e47b8ba46bbba23d0f8ff03a902 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300404670> .
        _:N3c1023bca87d4df3afb4a17c87a21236 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N6627f4dbe3de4ae9892b257245e18310 <http://www.cidoc-crm.org/cidoc-crm/P141_assigned> <https://id.rijksmuseum.nl/200140269> .
        _:Nc2b555ca9f6f41388073becf10aea022 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:N834d394a4d8140769b70024caf6d3850 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300404620> .
        _:Nbc6476862fc24fce8871a051a98d8932 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "1 x kroonlijst (U-vormig)" .
        _:N82cc48ea181f4b719a5df1a66123dc02 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:Nfebc8f394dae453391d1161bc0a9c8c0 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:N482dd2adec334db989fce4e1be63fe68 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:Nc9bb1c958c024f86bed9da3b7c8724fd <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "9" .
        _:Nf68b0b2a16044b53901390eed14c6ad3 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N62f58c5aebc74afd9ef9efa35aacbdb3 .
        _:Na1779b2ffa7f4b9989aa6b09c4e004d6 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "3" .
        _:N7acecaf459d14b8ba111553f6a9673b0 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N24f41bf40d8b4e4e9da094b0ac9974c8 .
        <https://id.rijksmuseum.nl/220149> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E57_Material> .
        _:Ne6fb6c600d3e4db5ba6325f7d36203b6 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E12_Production> .
        _:N1d603ad9502b4f6dbb792ca6713d922c <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300311954> .
        _:Nab29a88bd6624273b3e69f939bdc43d2 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388277> .
        <https://id.rijksmuseum.nl/500118801115697826580> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.ics.forth.gr/isl/CRMdig/D1_Digital_Object> .
        _:N17e116ac376c41eeaa1884c0e5713ca5 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "kroonlijst schouw: hoogte 80 cm (1 x kroonlijst (U-vormig))" .
        _:N64ba3c9b868147b8b0d0ff4ed4cd4e73 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:Nb9d8d388a0d740bc883fa0ef3581de24 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:N1f3bcdeb3f524aa996b98fc3dce46a9c <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        _:N09f93d0f42bc47a48d8f98adf5aa17ab <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "1626" .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P43_has_dimension> _:N6deccae762f543ff8edc6d030cf85cb1 .
        _:Nb4b2aae9d771492b84fefc048c75ce40 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300445022> .
        _:Nccfaeb94540c4421ab4975acb489d11f <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N32208ec5b9ce4b838a0d90897c98480f <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300445022> .
        _:N082f41fa1877442bb605fceb4dab9da7 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "instap bedstee: lengte 166 cm (1 x zijwand bedstee (instap bedstee))" .
        _:N3e185a0c0020413da970158c34c0d4cd <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        _:N5d861f12afca43e9879bd7bab9b16288 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435417> .
        _:N703c95b914c74d59b922c85de28417fe <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:N7f79f5380ec84a009fb337efe323e347 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "1 x console (zit op kolom)" .
        _:N0880a231761441dcbb57606e8decb557 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N0cb07388ba2a4f8c8344bfb6e024f3bc <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/22011> .
        <https://id.rijksmuseum.nl/220123> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E57_Material> .
        _:Naad832a2d3574eb9934e19146aaf96df <http://www.cidoc-crm.org/cidoc-crm/P90_has_value> "250" .
        _:N32a1df65f52342f28aefb91dc9064ede <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        <http://vocab.getty.edu/aat/300388277> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E56_Language> .
        _:N7a8f1bd8a5734f2aaf0f1692e26b79e3 <http://www.cidoc-crm.org/cidoc-crm/P82b_end_of_the_end> "2018-02-27T00:00:00Z"^^<http://www.w3.org/2001/XMLSchema#dateTime> .
        _:N55b3b20fb44e4d0f93fdd20f05245535 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N0aa35f5814a04ddc8992ec1a23c87509 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "1 x wandpaneel (van het rechterkopje mist de neus)" .
        _:N7ac2ff624a324d1d84f7a33274977e50 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:N2bc47437568e409fb8c222ab6e7be46f <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N5a1cb55c4e164ddca0ebb0b8f6d0a743 .
        _:Nff57fa74386646cf99bd1a83860f45af <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "height 250 cm" .
        _:N52401e5acd0a4bc5893b1bba3008cbba <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:Nfebc8f394dae453391d1161bc0a9c8c0 <http://www.cidoc-crm.org/cidoc-crm/P106_is_composed_of> _:N59a34bd195db4121918f1827bdfbf755 .
        <http://vocab.getty.edu/aat/300055863> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E55_Type> .
        _:N7a5d1eaef1a044429136dad2a15c9fac <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N45abc2b7fbd144e98e4caca8ea712536 .
        _:Nab29a88bd6624273b3e69f939bdc43d2 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "2018-02-27" .
        _:Nb37f04e0249540e194ad05cd81fea8c6 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N77c5f62bfe2b44019d055bd5fbf30d27 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N9ac58a8171204af78d71afbe70364eab .
        _:N658aff6bbc4d45db8b4b42450712f00e <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        _:N053403eb2d9e45f99f1da036db71b1ee <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "height 98 cm" .
        _:N2bcf69baf4334e1bb1ebfba3e5a96afc <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/22012> .
        _:N1a462cc9f2b142a3ad30e821b9193592 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/2203> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P43_has_dimension> _:N4ea6864a30394ca09e8e1f8ef3a51a53 .
        <http://vocab.getty.edu/aat/300379098> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E58_Measurement_Unit> .
        _:N081d86ce2eb84d278ef8fd2ef77bdf03 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "HG" .
        _:Naecfa816892c49c38a92d7eadfa75ae4 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",,: breedte 132,5 cm (,,) x breedte 133,5 cm (,,) x breedte 60 cm (,,) x diepte 11 cm (,,) x breedte 110 cm (,,) x diepte 5 cm (,,) x breedte 173 cm (,,) x diepte 5 cm (,,) x breedte 73 cm (,,) x diepte 5 cm (,,) x breedte 250 cm (,,) x diepte 80 cm (,,) x breedte 22 cm (,,) x diepte 60 cm (,,) x breedte 15 cm (,,) x diepte 15 cm (,,) x breedte 20 cm (,,) x diepte 9 cm (,,) x breedte 20 cm (,,) x diepte 38 cm (,,) x breedte 22 cm (,,) x diepte 60 cm (,,) x breedte 20 cm (,,) x diepte 9 cm (,,) x breedte 30 cm (,,) x diepte 38 cm (,,)" .
        _:Ne05c7d06eea84c4691999a4d6bf8f4a9 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300456575> .
        _:N482dd2adec334db989fce4e1be63fe68 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300445022> .
        _:Nfbbd7c56a7e241ac8565ff0e8a1500d5 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388277> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P43_has_dimension> _:N187de5db104b498285561e41ac556499 .
        _:Ne6fb6c600d3e4db5ba6325f7d36203b6 <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N11eedb37d5ea4da598e5e788962d483b .
        _:N054da200073441e0adbbdd9d84fc4568 <http://www.cidoc-crm.org/cidoc-crm/P90_has_value> "250" .
        _:N601e00fa88834f91ba480248515ee765 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388277> .
        _:N5151ca6daaeb4a48ac8c1a44279166a6 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        _:Nc4ddfca1ccc14e5eb07dd27528790a0d <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "Dordrecht, 1626, various woods" .
        _:N6b0dee5761c544e7bdca4844a780cac1 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E54_Dimension> .
        _:Nb362ca7497fe44d5bebcd2e665a7c9d3 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        <http://vocab.getty.edu/aat/300388256> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E56_Language> .
        _:N434683045bf941e7ae1c3876c356377b <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E54_Dimension> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P45_consists_of> <https://id.rijksmuseum.nl/2201452> .
        <https://id.rijksmuseum.nl/30125657> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N27a101c38ecc45a2a456bfb43524f36e <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "Betimmering van eikenhout, versierd met intarsia van ebbenhout, buxus- en esdoornhout en palissander." .
        _:N82cc48ea181f4b719a5df1a66123dc02 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P43_has_dimension> _:N93137abd12e24f8d8a6ae1da855876cd .
        _:Nf4d33be5acfb487182a4cc317eac39f3 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E30_Right> .
        _:N47f956f64efc4a91a391e3f6cde786f6 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300312355> .
        <http://vocab.getty.edu/aat/300435430> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E55_Type> .
        _:Na4ed40dc21804706b623189d751b6fd1 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N01be04987df14fdfbb1f874333ae213b .
        _:Na5e61396949640109227da3a437d15fe <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:Ne5cbbc8733434408a0600147fede319b <http://www.cidoc-crm.org/cidoc-crm/P141i_was_assigned_by> _:Nb33e6c41d95f4ecc964e87baf318bb30 .
        _:N2610e69ebd804846b591e4014a84fdc8 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "5" .
        _:Nf7dbe80f8d4b46d680024f9ab39b50e6 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E13_Attribute_Assignment> .
        _:Ncd301494c82849caba4115a0d298fade <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N6d31805660c34ca194154a5df206a7de .
        _:N77c5f62bfe2b44019d055bd5fbf30d27 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388277> .
        _:Nb362ca7497fe44d5bebcd2e665a7c9d3 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "zijwand bedstee" .
        _:Nb7490660783349da8c8f3584b200fdb1 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300311954> .
        _:Nd34ef77968e842e7bc2a73e11504b287 <http://www.cidoc-crm.org/cidoc-crm/P91_has_unit> <http://vocab.getty.edu/aat/300379098> .
        _:N119d6c758d544f1894f6dd0f34450571 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435416> .
        _:N6554fa7e891d42f5b2d66091751fdbab <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E54_Dimension> .
        _:Nf41ddfb3b37748b1855b424b6032fe40 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N33730449371c4173a22a9814bef22a21 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "2" .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N326aae03a4974a92953f4f3132f7c866 .
        _:Na2302e47b8ba46bbba23d0f8ff03a902 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P43_has_dimension> _:N2bcf69baf4334e1bb1ebfba3e5a96afc .
        _:N0cb07388ba2a4f8c8344bfb6e024f3bc <http://www.cidoc-crm.org/cidoc-crm/P91_has_unit> <http://vocab.getty.edu/aat/300379098> .
        _:N0a8fcf512a7b48c88b3052d21f2eff1a <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:Ndc9392ef2fd84fd78a5ab569d96a9b8c <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "Publieke domein" .
        _:N11f9777424e34080a6f34cddd051c1cf <http://www.cidoc-crm.org/cidoc-crm/P141_assigned> _:Nf68b0b2a16044b53901390eed14c6ad3 .
        _:N0cd9a3d62b8a4d2eb55832a64919dfdd <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "Flemish influences" .
        _:N9fac90d69ab74000b3ec6ce5db36a70c <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:N67eab31835754e12837562bab5f500a0 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300456575> .
        _:N47f956f64efc4a91a391e3f6cde786f6 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/22015218> .
        _:N608dde33f09f49f4817df74612a94b78 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/22012> .
        _:Naecfa816892c49c38a92d7eadfa75ae4 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:Nf2aab31ea1b1439790f47ac2d24b974e .
        _:Nd9ddd9258d3a461aa9eb7aac209a5210 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N2bcf69baf4334e1bb1ebfba3e5a96afc <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:Nc2555581e07b470f9ae3c85d2c5bc75f .
        _:N0aa35f5814a04ddc8992ec1a23c87509 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N1a6332eb389645caa5a17dde503440be <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N1f052b21ce384a30a45e2679f813b4df <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388277> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/220432> .
        _:N1b3ed30ab1d848b183ae623b1b6f73e8 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:Nbe07f34c77ad43998e8b66a13184cfee <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:Nf57ec8fb8c364c9dad7c26971e3e956a <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:N0cab1d0fb97a4a58a25c186a712a3276 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:Ncf59d64c146f4b54bdf1e2e0d57bfa66 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "1 x voetstuk linker kolom" .
        <https://id.rijksmuseum.nl/210640> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E39_Actor> .
        _:Nd91c97946f9544deba324bdfa2acf583 <http://www.cidoc-crm.org/cidoc-crm/P91_has_unit> <http://vocab.getty.edu/aat/300379098> .
        _:Na2a8b3c2453e4826b1f8b1ac821736ab <http://www.cidoc-crm.org/cidoc-crm/P106_is_composed_of> _:N1c6a400b9d1c4264953b51c48725e82a .
        _:Nff57fa74386646cf99bd1a83860f45af <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N52401e5acd0a4bc5893b1bba3008cbba <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N1a6332eb389645caa5a17dde503440be <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        <https://id.rijksmuseum.nl/242140269> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E7_Activity> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N77c5f62bfe2b44019d055bd5fbf30d27 .
        _:N2d00c5101f844d34acd31d2b253a4282 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:N2ced60f46cdd4ab3a6f14354d9fd817d <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:N10991c13ecad4042b6f74897010a2fd5 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E54_Dimension> .
        _:N5d89ec6c9e8e4da5ae945adc33afe621 <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N1f3bcdeb3f524aa996b98fc3dce46a9c .
        _:N6d31805660c34ca194154a5df206a7de <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        _:N1cb7a3434e7c4805a84b96fd1cb75cba <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E54_Dimension> .
        _:Nc2ab8d49b551404e9a60d49b2dca3862 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/22012> .
        <https://id.rijksmuseum.nl/2202603> <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435443> .
        _:Nc5f8aa4aa4714fddadb069e47a3f3e8f <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388277> .
        _:N68141ab26c3c49509b68406b177ee851 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "2 x kolom (marmer)" .
        <http://vocab.getty.edu/aat/300418049> <http://www.w3.org/2000/01/rdf-schema#label> "brief text" .
        _:N3b2a98dbac624848ac3dd47af776626b <http://www.cidoc-crm.org/cidoc-crm/P141_assigned> <https://id.rijksmuseum.nl/200140269> .
        _:Ne6fb6c600d3e4db5ba6325f7d36203b6 <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N5d861f12afca43e9879bd7bab9b16288 .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P141i_was_assigned_by> _:Nb7490660783349da8c8f3584b200fdb1 .
        _:Ncf3c779254b84e9fb3da285617b4e7e7 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "paneel rechts schouw: hoogte 250 cm (1 x wandpaneel)" .
        _:N74c857482c264766ad5f98cabbd270f1 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:Nf41ddfb3b37748b1855b424b6032fe40 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:Nf1f87055185b4ede9449784a331c65c4 .
        _:Nfcb44b36ba5f4e2e95f6ce192f5e1da6 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:Nff57fa74386646cf99bd1a83860f45af <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:Nf15f848ab09a454486a027f9af75f2f0 .
        _:N2fdf9d11a66045daafc63715d749a4e4 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:Na2302e47b8ba46bbba23d0f8ff03a902 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388277> .
        _:N4841974218ed4f44b01113de5a960a2a <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:Nd9ddd9258d3a461aa9eb7aac209a5210 .
        _:N9ac58a8171204af78d71afbe70364eab <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300456575> .
        _:N326aae03a4974a92953f4f3132f7c866 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N2d00c5101f844d34acd31d2b253a4282 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "height 80 cm" .
        _:N80a9d20c250c4bf98625378781048e22 <http://www.cidoc-crm.org/cidoc-crm/P90_has_value> "38" .
        _:Ne6fb6c600d3e4db5ba6325f7d36203b6 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N28b554b5d861495b9f4272a99abf118c .
        _:Ncd301494c82849caba4115a0d298fade <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/2203> .
        _:N616b457f812f4e1696ba92dd99bc1989 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N35e44becd20b419593d5ff5efe283bd0 .
        _:Nbd32e6417f644bc4bbe678599a84d9a1 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:N47f956f64efc4a91a391e3f6cde786f6 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:N372342e34bde4672836392b9ea4bcfac <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        _:N608dde33f09f49f4817df74612a94b78 <http://www.cidoc-crm.org/cidoc-crm/P91_has_unit> <http://vocab.getty.edu/aat/300379098> .
        _:N3bbcf21a24c742db8dc5f96f96589c3a <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N705c4d6a6699417995110eaab1c55117 .
        _:N3bbcf21a24c742db8dc5f96f96589c3a <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        _:N1ac61619e0104c48bc0939096b9d3d98 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300456575> .
        _:N985540f659474407a218059a2bc49b7d <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:Nb0062b0bf6ad47fa9357e4598b8dc73f <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "wandpaneel: hoogte 250 cm (1 x wandpaneel (van het rechterkopje mist de neus))" .
        _:N08a0cc3dd9c54665a6eded9e92a8c5bc <http://www.cidoc-crm.org/cidoc-crm/P177_assigned_property_of_type> <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> .
        _:N2d5a5881f1f844a9949c76113b67c0d7 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "1877" .
        _:Nbe07f34c77ad43998e8b66a13184cfee <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "1 x console (zit op kolom)" .
        _:Ne6fb6c600d3e4db5ba6325f7d36203b6 <http://www.cidoc-crm.org/cidoc-crm/P7_took_place_at> <https://id.rijksmuseum.nl/230171> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N47f956f64efc4a91a391e3f6cde786f6 .
        _:Ne89c0c29dfa74d4dbb7770cc84a4304b <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N6554fa7e891d42f5b2d66091751fdbab <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/22011> .
        _:N6f6d1d215da54c718f7bcbf200bdeb70 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388277> .
        _:Nb7490660783349da8c8f3584b200fdb1 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E13_Attribute_Assignment> .
        <https://id.rijksmuseum.nl/2201452> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E57_Material> .
        _:N616b457f812f4e1696ba92dd99bc1989 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/2203> .
        <http://vocab.getty.edu/aat/300379475> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E55_Type> .
        _:Nf65276a3f25d4ade99a6af1dd57092ff <http://www.cidoc-crm.org/cidoc-crm/P106_is_composed_of> _:N912e95b047ed4f699f1ff3e7076fd903 .
        _:Ne6fb6c600d3e4db5ba6325f7d36203b6 <http://www.cidoc-crm.org/cidoc-crm/P32_used_general_technique> <https://id.rijksmuseum.nl/2205597> .
        <https://id.rijksmuseum.nl/220907> <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N885109c17a1840c8bc48ebc3a6426581 .
        _:N658aff6bbc4d45db8b4b42450712f00e <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        <http://vocab.getty.edu/aat/300004188> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E55_Type> .
        _:N6554fa7e891d42f5b2d66091751fdbab <http://www.cidoc-crm.org/cidoc-crm/P90_has_value> "32" .
        _:N2d5a5881f1f844a9949c76113b67c0d7 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388277> .
        _:N6c6d3829ad7b40f4b98b8e3f2661b011 <http://www.cidoc-crm.org/cidoc-crm/P106_is_composed_of> _:Nb412bc5b75614a6b9f89b97a4c6b71e1 .
        _:Na467b5ec285348b9a5549ba677c13dba <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E13_Attribute_Assignment> .
        _:N82590e8f23af4251a37c031c32f125dc <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N32a1df65f52342f28aefb91dc9064ede .
        _:Na2163ebe97c249608fda081dd3ab24a0 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N68141ab26c3c49509b68406b177ee851 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        <https://id.rijksmuseum.nl/202140269> <http://www.cidoc-crm.org/cidoc-crm/P138_represents> <https://id.rijksmuseum.nl/230171> .
        _:N1cb7a3434e7c4805a84b96fd1cb75cba <http://www.cidoc-crm.org/cidoc-crm/P90_has_value> "133.5" .
        _:N5d89ec6c9e8e4da5ae945adc33afe621 <http://www.cidoc-crm.org/cidoc-crm/P91_has_unit> <http://vocab.getty.edu/aat/300379098> .
        _:N345d67f33b8443c9aef51ae71ff22990 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/2203> .
        _:N10991c13ecad4042b6f74897010a2fd5 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/22011> .
        _:Nc9bb1c958c024f86bed9da3b7c8724fd <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:Nbe7f9e24a4044ddba9a04c8af14b8cb8 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:Nfbbd7c56a7e241ac8565ff0e8a1500d5 .
        _:N081d86ce2eb84d278ef8fd2ef77bdf03 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300004188> .
        _:N68dee9dbffc4437d8539b0964f13a7eb <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:Na7bfabc7e26645d4bf6702b2a89ebe38 <http://www.cidoc-crm.org/cidoc-crm/P91_has_unit> <http://vocab.getty.edu/aat/300379098> .
        _:N541427f2d233458e9bc8084d00f36fc3 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        _:N703c95b914c74d59b922c85de28417fe <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "6" .
        _:Ne5cbbc8733434408a0600147fede319b <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "7" .
        _:N62373814cc20414594e8e2d863115be4 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:N1f052b21ce384a30a45e2679f813b4df <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "17th Century" .
        _:Ne6c70d7bc3994992a5e7cb760221e390 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "12" .
        _:Nd91c97946f9544deba324bdfa2acf583 <http://www.cidoc-crm.org/cidoc-crm/P90_has_value> "166" .
        _:N3e08df9af24c40f58afdcff60e1f30be <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:N3f0071080f814903b65c8093e0b87567 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:N616b457f812f4e1696ba92dd99bc1989 <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N5dd0d1de24294ec5a2b1f9b4c025be51 .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N0bd6f8641bfd4752ae8f824aff7758fe .
        _:N3b8054b7b5944f5483da63d105d116ac <http://www.cidoc-crm.org/cidoc-crm/P90_has_value> "60" .
        _:Ne89c0c29dfa74d4dbb7770cc84a4304b <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        _:N6c6d3829ad7b40f4b98b8e3f2661b011 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435449> .
        _:Nfd49546aacb1470594f93824a9041c17 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:N3ad1d58543eb469d8f0644d22387f287 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P43_has_dimension> _:N5452c79ad18548d59c42e3844d13a003 .
        _:N46e350cf3cb44e98a607d8f54ea4f04c <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N2b43b56170b14dd3914425a5e264d3c8 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300417268> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P43_has_dimension> _:Nd34ef77968e842e7bc2a73e11504b287 .
        _:Na9cacc1829df47ecb369f81d1bc11693 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300404620> .
        _:N6ec0951cf9844dd6840ed80331795ac6 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:N09412cb461ed4f19bb7390358576be19 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:Nc21e4df26d3f4c409540c3d9882f7a2c <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N62373814cc20414594e8e2d863115be4 .
        _:N985540f659474407a218059a2bc49b7d <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300445022> .
        <https://id.rijksmuseum.nl/30166252> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:Nc4169ea2b4ce432794ea787e61e94c88 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:Nd86696de53aa469b86c73313045ef311 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        <https://id.rijksmuseum.nl/2202604> <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:Nf12eee99ea474b61956284e5b4b3e03f .
        _:N602fd592d77646408d865835ee712135 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N2199894fb15e4d7e82b807925e431e62 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:Nf57ec8fb8c364c9dad7c26971e3e956a .
        _:N11f9777424e34080a6f34cddd051c1cf <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E13_Attribute_Assignment> .
        _:Nbd1e5854266f4be8971af77ce121fe39 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "1877" .
        _:Na2302e47b8ba46bbba23d0f8ff03a902 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "Wainscoting with chimneypiece, wallpanels and a portico" .
        _:Nd0da0cd3b0bf4e04833992add79cd921 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:Ne5b410b375df4ebda580183a7ae699d6 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N15d3ed5dcbf343539b6bafec92e4a3d6 .
        <http://vocab.getty.edu/aat/300312355> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E55_Type> .
        _:Nb7490660783349da8c8f3584b200fdb1 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N4bec33370efd46e8a61e1adb740013a9 .
        _:Ne1f2017392124d449f1d5c2b65ed01c2 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N434683045bf941e7ae1c3876c356377b <http://www.cidoc-crm.org/cidoc-crm/P91_has_unit> <http://vocab.getty.edu/aat/300379098> .
        _:N09ddaca824f34874be53c19746261aaa <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "kolom schouw: hoogte 98 cm (2 x kolom (marmer))" .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/2202603> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P45_consists_of> <https://id.rijksmuseum.nl/2203658> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P129i_is_subject_of> _:N2b43b56170b14dd3914425a5e264d3c8 .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:Ne5b410b375df4ebda580183a7ae699d6 .
        _:Na2302e47b8ba46bbba23d0f8ff03a902 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300417207> .
        _:N3c1023bca87d4df3afb4a17c87a21236 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "diverse houtsoorten" .
        _:N430e162d4f5e44f2a83395ebdaeb7eb6 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "afb. XI-XII" .
        _:Ndbb8fc769442469c89fcfafae4d956d3 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:Nf7dbe80f8d4b46d680024f9ab39b50e6 <http://www.cidoc-crm.org/cidoc-crm/P177_assigned_property_of_type> <http://www.cidoc-crm.org/cidoc-crm/P15_was_influenced_by> .
        _:N55b3b20fb44e4d0f93fdd20f05245535 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435430> .
        _:N885109c17a1840c8bc48ebc3a6426581 <http://www.cidoc-crm.org/cidoc-crm/P141i_was_assigned_by> _:Nc0730d8c31044cfb88248a7c618c1fe4 .
        _:N5d861f12afca43e9879bd7bab9b16288 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        <https://id.rijksmuseum.nl/260212> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://linked.art/ns/terms/Set> .
        _:N54379e36dc604eca9c327c7841436c2e <http://www.cidoc-crm.org/cidoc-crm/P90_has_value> "110" .
        _:Nf15f848ab09a454486a027f9af75f2f0 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:N22aa8fbc2b2e47b9b9fea725fad48065 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E12_Production> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:Ne1f2017392124d449f1d5c2b65ed01c2 .
        _:N2b43b56170b14dd3914425a5e264d3c8 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:Ne359204a393a4afeaeb69ed89ea83ded <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "1" .
        _:N6d361e0d732e413e80b8df766c403fcc <http://www.cidoc-crm.org/cidoc-crm/P90_has_value> "60" .
        _:N885109c17a1840c8bc48ebc3a6426581 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "2" .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P141i_was_assigned_by> _:N08a0cc3dd9c54665a6eded9e92a8c5bc .
        _:N81413029a74e471d884349daca1067ce <http://www.cidoc-crm.org/cidoc-crm/P106i_forms_part_of> <https://id.rijksmuseum.nl/301100936> .
        _:N09f93d0f42bc47a48d8f98adf5aa17ab <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        _:N7987dfeff72a4a079682b0fc0ef2adcc <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E54_Dimension> .
        _:N326aae03a4974a92953f4f3132f7c866 <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:Nf004dd8e9ac64490b4f1d9f3f1009b2f .
        _:N6554fa7e891d42f5b2d66091751fdbab <http://www.cidoc-crm.org/cidoc-crm/P91_has_unit> <http://vocab.getty.edu/aat/300379098> .
        _:N5dd0d1de24294ec5a2b1f9b4c025be51 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N7acecaf459d14b8ba111553f6a9673b0 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E54_Dimension> .
        _:N0cb07388ba2a4f8c8344bfb6e024f3bc <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N68141ab26c3c49509b68406b177ee851 .
        _:N912e95b047ed4f699f1ff3e7076fd903 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N9d83116074a84c1aba09f08548b4b6a6 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:N1c6a400b9d1c4264953b51c48725e82a <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:N3fa85c9e0991441ead5f544faf65e1c9 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        _:Ndbb8fc769442469c89fcfafae4d956d3 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:Ncf3c779254b84e9fb3da285617b4e7e7 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N0a8fcf512a7b48c88b3052d21f2eff1a <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        _:Nf24b745418814730b2b21f19f5ab63ec <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> ",," .
        _:N24a73ce7bd9b49c6ba1155d2578dac6a <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388277> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:Ncf3c779254b84e9fb3da285617b4e7e7 .
        _:N3ad1d58543eb469d8f0644d22387f287 <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300260522> .
        _:N0585088e0a45457485e54372541fb56a <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N175af0468c494b01bc82752ab8b10c39 .
        <https://id.rijksmuseum.nl/301100936> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N6b20b0bc4ce8442f87e5e14187a5e606 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N6ec0951cf9844dd6840ed80331795ac6 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:Nb542bdb6c71c4f2d8e69c260634d9d07 <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N602fd592d77646408d865835ee712135 .
        _:N372342e34bde4672836392b9ea4bcfac <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_E41_Linguistic_Appellation> .
        <https://id.rijksmuseum.nl/220432> <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://vocab.getty.edu/aat/300435443> .
        _:N0e02d5ecb0d74c889cd09a38a989ef88 <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "vervaardiger: anonymous, Dordrecht" .
        _:N10991c13ecad4042b6f74897010a2fd5 <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N1acc4d99a6674bdb9822837fc642ab16 .
        _:N608dde33f09f49f4817df74612a94b78 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E54_Dimension> .
        _:N027a25da94e04bc0bd578b276c45ce92 <http://www.cidoc-crm.org/cidoc-crm/P90_has_value> "15" .
        _:Nb0062b0bf6ad47fa9357e4598b8dc73f <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:N9fac90d69ab74000b3ec6ce5db36a70c <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "6" .
        _:Ne6fb6c600d3e4db5ba6325f7d36203b6 <http://www.cidoc-crm.org/cidoc-crm/P14_carried_out_by> <https://id.rijksmuseum.nl/210640> .
        _:N5dd0d1de24294ec5a2b1f9b4c025be51 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:Na2e28bbaa6ed4a4cab5c09738fd06bfa <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> _:N2e450d51dde940b4960a72714bb2d9d9 .
        _:N7a8f1bd8a5734f2aaf0f1692e26b79e3 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E52_Time-Span> .
        _:N6d31805660c34ca194154a5df206a7de <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N18477e1a18684649b862535722c3366b <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier> .
        _:N082f41fa1877442bb605fceb4dab9da7 <http://www.cidoc-crm.org/cidoc-crm/P72_has_language> <http://vocab.getty.edu/aat/300388256> .
        _:Nb9d8d388a0d740bc883fa0ef3581de24 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E33_Linguistic_Object> .
        _:N37947258001e4fe886ef5e16ee8d098b <http://www.cidoc-crm.org/cidoc-crm/P67i_is_referred_to_by> _:N2ac9912314b0440abca8ea7ad2d0b40f .
        _:N2ced60f46cdd4ab3a6f14354d9fd817d <http://www.cidoc-crm.org/cidoc-crm/P190_has_symbolic_content> "1 x wandpaneel" .
        _:N37947258001e4fe886ef5e16ee8d098b <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E54_Dimension> .
        <https://id.rijksmuseum.nl/200140269> <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://id.rijksmuseum.nl/2201073> .
        _:N5452c79ad18548d59c42e3844d13a003 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E54_Dimension> .
    '''

    g = Graph().parse(data=ntriples, format='nt')

    start = datetime.now()
    t_original = canonicalize_triples(g, False)
    t_original_time = (datetime.now() - start).total_seconds()

    start = datetime.now()
    t_optimized = canonicalize_triples(g, True)
    t_optimized_time = (datetime.now() - start).total_seconds()

    assert t_original == t_optimized, "Optimized version deviates from original on critical edge case"
    assert t_optimized_time < 4, "Optimized execution time"

def test_failure_case_exposes_difference():
    """
    This graph has symmetrical bnodes with identical structure and values.
    Only the original version explores all individuation paths to reach discrete coloring.
    """
    n3 = """
    @prefix : <http://example.org/> .

    :root :p _:a, _:b, _:c .

    _:a :p :leaf .
    _:b :p :leaf .
    _:c :p :leaf .
    """
    g = Graph().parse(data=n3, format="n3")
    t_original = canonicalize_triples(g, use_improved=False)
    t_optimized = canonicalize_triples(g, use_improved=True)
    assert t_original == t_optimized, "Optimized version fails to canonicalize symmetric bnode structure like original"


EX = Namespace("http://example.org/")


def generate_symmetric_graph(num_bnodes: int, use_labels: bool = False) -> Graph:
    g = Graph()
    bnodes = [BNode() for _ in range(num_bnodes)]
    
    # Connect all bnodes in a full loop
    for i in range(num_bnodes):
        g.add((bnodes[i], EX.connect, bnodes[(i + 1) % num_bnodes]))
    
    # Attach same predicate to a common root node
    for b in bnodes:
        g.add((EX.root, EX.connect, b))

    # Optionally label them the same (for further symmetry)
    if use_labels:
        for b in bnodes:
            g.add((b, EX.label, Literal("X")))
    
    return g


@pytest.mark.parametrize("use_labels", [False, True])
@pytest.mark.parametrize("num_bnodes", [3, 4, 5, 50])
def test_random_symmetric_graphs(num_bnodes, use_labels):
    """
    Fuzz test with perfectly symmetric graphs. These should canonicalize identically.
    """
    g = generate_symmetric_graph(num_bnodes=num_bnodes, use_labels=use_labels)
    t_original = canonicalize_triples(g, use_improved=False)
    t_optimized = canonicalize_triples(g, use_improved=True)
    assert t_original == t_optimized, (
        f"Mismatch in canonicalization for symmetric graph with {num_bnodes} bnodes.\n"
        f"Use labels: {use_labels}"
    )

def test_mandatory_path_exploration_case():
    """
    This graph requires exploring multiple equal-score individuation paths
    to reach a canonical form. Optimized _traces2 picks one and may fail.
    """
    n3 = """
    @prefix : <http://example.org/> .

    :root :knows _:a, _:b, _:c .

    _:a :knows _:b .
    _:b :knows _:c .
    _:c :knows _:a .

    _:a :label "friend" .
    _:b :label "friend" .
    _:c :label "friend" .
    """
    g = Graph().parse(data=n3, format="n3")
    t_orig = canonicalize_triples(g, use_improved=False)
    t_opt = canonicalize_triples(g, use_improved=True)

    assert t_orig == t_opt, "Optimized version failed to handle path-sensitive individuation properly"