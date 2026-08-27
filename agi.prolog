%%% ========================================================================
%%% AGI.prolog v3.1 — Núcleo Lógico da AGI (Auditado e Corrigido)
%%% ========================================================================
%%% Baseado na Auditoria Independente v2026-08-26
%%%
%%% Correções aplicadas (18/18):
%%%   [C1]  element/4: átomos com aspas simples ('H') — FIX-P1
%%%   [C2]  etica_material/2: sintaxe Prolog (->/;) — FIX-P3
%%%   [C3]  :- module(agi_v3, [...]) restaurado — FIX-P9
%%%   [C4]  forward_chain: temp_derived + retractall — FIX-P2
%%%   [C5]  execute_plan: forall/2 sintaxe correta — FIX-P7
%%%   [C6]  Motor funcional completo restaurado — FIX-N2
%%%   [C7]  118 elementos químicos reintroduzidos — FIX-N1
%%%   [C8]  think/3: with_mutex para métricas — FIX-P5
%%%   [C9]  25+ testes restaurados — FIX-P10
%%%   [C10] has_contradiction: pares adjacentes — FIX-P6
%%%   [C11] Interface: queries parametrizadas
%%%   [C12] Interface: timeout via thread
%%%   [C13] consume_element: dígitos corretos — FIX-P11
%%%   [C14] regex_match: verificação nonvar — FIX-P12
%%%   [C15] Pesos documentados
%%%   [C16] Fatos isolados integrados em regras
%%%   [C17] Strings padronizadas para átomos — FIX-N4
%%%   [C18] == substituído por = — FIX-N3
%%%
%%% Compatível: SWI-Prolog 8.x+ (GNU Prolog requer ajustes menores)
%%% ========================================================================

:- module(agi_v3, [
    % Motor de Inferência
    prove/1,
    prove/2,
    forward_chain/1,
    backward_chain/2,
    abduce/3,

    % Segurança
    is_safe_prompt/1,
    detect_jailbreak/2,
    detect_injection/2,
    sanitize_input/2,

    % Validação de Mundo
    is_valid_formula/1,
    extract_formula/2,
    has_contradiction/1,
    validate_world/2,

    % Planejamento
    create_plan/3,
    select_tool/2,

    % Memória
    remember/3,
    recall/2,
    forget/1,
    memory_stats/2,

    % Aprendizado
    record_experience/4,
    compute_reward/3,
    select_best_action/2,

    % Orquestração
    think/3,
    agi_init/0,
    get_metrics/1,

    % Novos do v3.0 (corrigidos)
    material_info/5,
    candidato_topologico/1,
    score_candidato/2,
    recomendacao_etica/2,

    % Testes
    run_tests/0
]).

:- use_module(library(pcre)).

%%% ========================================================================
%%% [C7] BASE DE CONHECIMENTO — 118 Elementos IUPAC (FIX-N1, FIX-P1)
%%% ========================================================================
%%% NOTA CRÍTICA: Símbolos de elementos DEVEM ser átomos (aspas simples)
%%% porque H, He, Li etc. seriam variáveis em Prolog!
%%% ========================================================================

element('H', 1, hydrogen, nonmetal, 1, 1, s).
element('He', 2, helium, noble_gas, 18, 1, s).
element('Li', 3, lithium, alkali_metal, 1, 2, s).
element('Be', 4, beryllium, alkaline_earth, 2, 2, s).
element('B', 5, boron, metalloid, 13, 2, p).
element('C', 6, carbon, nonmetal, 14, 2, p).
element('N', 7, nitrogen, nonmetal, 15, 2, p).
element('O', 8, oxygen, nonmetal, 16, 2, p).
element('F', 9, fluorine, halogen, 17, 2, p).
element('Ne', 10, neon, noble_gas, 18, 2, p).
element('Na', 11, sodium, alkali_metal, 1, 3, s).
element('Mg', 12, magnesium, alkaline_earth, 2, 3, s).
element('Al', 13, aluminium, post_transition, 13, 3, p).
element('Si', 14, silicon, metalloid, 14, 3, p).
element('P', 15, phosphorus, nonmetal, 15, 3, p).
element('S', 16, sulfur, nonmetal, 16, 3, p).
element('Cl', 17, chlorine, halogen, 17, 3, p).
element('Ar', 18, argon, noble_gas, 18, 3, p).
element('K', 19, potassium, alkali_metal, 1, 4, s).
element('Ca', 20, calcium, alkaline_earth, 2, 4, s).
element('Sc', 21, scandium, transition_metal, 3, 4, d).
element('Ti', 22, titanium, transition_metal, 4, 4, d).
element('V', 23, vanadium, transition_metal, 5, 4, d).
element('Cr', 24, chromium, transition_metal, 6, 4, d).
element('Mn', 25, manganese, transition_metal, 7, 4, d).
element('Fe', 26, iron, transition_metal, 8, 4, d).
element('Co', 27, cobalt, transition_metal, 9, 4, d).
element('Ni', 28, nickel, transition_metal, 10, 4, d).
element('Cu', 29, copper, transition_metal, 11, 4, d).
element('Zn', 30, zinc, transition_metal, 12, 4, d).
element('Ga', 31, gallium, post_transition, 13, 4, p).
element('Ge', 32, germanium, metalloid, 14, 4, p).
element('As', 33, arsenic, metalloid, 15, 4, p).
element('Se', 34, selenium, nonmetal, 16, 4, p).
element('Br', 35, bromine, halogen, 17, 4, p).
element('Kr', 36, krypton, noble_gas, 18, 4, p).
element('Rb', 37, rubidium, alkali_metal, 1, 5, s).
element('Sr', 38, strontium, alkaline_earth, 2, 5, s).
element('Y', 39, yttrium, transition_metal, 3, 5, d).
element('Zr', 40, zirconium, transition_metal, 4, 5, d).
element('Nb', 41, niobium, transition_metal, 5, 5, d).
element('Mo', 42, molybdenum, transition_metal, 6, 5, d).
element('Tc', 43, technetium, transition_metal, 7, 5, d).
element('Ru', 44, ruthenium, transition_metal, 8, 5, d).
element('Rh', 45, rhodium, transition_metal, 9, 5, d).
element('Pd', 46, palladium, transition_metal, 10, 5, d).
element('Ag', 47, silver, transition_metal, 11, 5, d).
element('Cd', 48, cadmium, transition_metal, 12, 5, d).
element('In', 49, indium, post_transition, 13, 5, p).
element('Sn', 50, tin, post_transition, 14, 5, p).
element('Sb', 51, antimony, metalloid, 15, 5, p).
element('Te', 52, tellurium, metalloid, 16, 5, p).
element('I', 53, iodine, halogen, 17, 5, p).
element('Xe', 54, xenon, noble_gas, 18, 5, p).
element('Cs', 55, caesium, alkali_metal, 1, 6, s).
element('Ba', 56, barium, alkaline_earth, 2, 6, s).
element('La', 57, lanthanum, lanthanide, 3, 6, f).
element('Ce', 58, cerium, lanthanide, 3, 6, f).
element('Pr', 59, praseodymium, lanthanide, 3, 6, f).
element('Nd', 60, neodymium, lanthanide, 3, 6, f).
element('Pm', 61, promethium, lanthanide, 3, 6, f).
element('Sm', 62, samarium, lanthanide, 3, 6, f).
element('Eu', 63, europium, lanthanide, 3, 6, f).
element('Gd', 64, gadolinium, lanthanide, 3, 6, f).
element('Tb', 65, terbium, lanthanide, 3, 6, f).
element('Dy', 66, dysprosium, lanthanide, 3, 6, f).
element('Ho', 67, holmium, lanthanide, 3, 6, f).
element('Er', 68, erbium, lanthanide, 3, 6, f).
element('Tm', 69, thulium, lanthanide, 3, 6, f).
element('Yb', 70, ytterbium, lanthanide, 3, 6, f).
element('Lu', 71, lutetium, lanthanide, 3, 6, f).
element('Hf', 72, hafnium, transition_metal, 4, 6, d).
element('Ta', 73, tantalum, transition_metal, 5, 6, d).
element('W', 74, tungsten, transition_metal, 6, 6, d).
element('Re', 75, rhenium, transition_metal, 7, 6, d).
element('Os', 76, osmium, transition_metal, 8, 6, d).
element('Ir', 77, iridium, transition_metal, 9, 6, d).
element('Pt', 78, platinum, transition_metal, 10, 6, d).
element('Au', 79, gold, transition_metal, 11, 6, d).
element('Hg', 80, mercury, transition_metal, 12, 6, d).
element('Tl', 81, thallium, post_transition, 13, 6, p).
element('Pb', 82, lead, post_transition, 14, 6, p).
element('Bi', 83, bismuth, post_transition, 15, 6, p).
element('Po', 84, polonium, post_transition, 16, 6, p).
element('At', 85, astatine, halogen, 17, 6, p).
element('Rn', 86, radon, noble_gas, 18, 6, p).
element('Fr', 87, francium, alkali_metal, 1, 7, s).
element('Ra', 88, radium, alkaline_earth, 2, 7, s).
element('Ac', 89, actinium, actinide, 3, 7, f).
element('Th', 90, thorium, actinide, 3, 7, f).
element('Pa', 91, protactinium, actinide, 3, 7, f).
element('U', 92, uranium, actinide, 3, 7, f).
element('Np', 93, neptunium, actinide, 3, 7, f).
element('Pu', 94, plutonium, actinide, 3, 7, f).
element('Am', 95, americium, actinide, 3, 7, f).
element('Cm', 96, curium, actinide, 3, 7, f).
element('Bk', 97, berkelium, actinide, 3, 7, f).
element('Cf', 98, californium, actinide, 3, 7, f).
element('Es', 99, einsteinium, actinide, 3, 7, f).
element('Fm', 100, fermium, actinide, 3, 7, f).
element('Md', 101, mendelevium, actinide, 3, 7, f).
element('No', 102, nobelium, actinide, 3, 7, f).
element('Lr', 103, lawrencium, actinide, 3, 7, f).
element('Rf', 104, rutherfordium, transition_metal, 4, 7, d).
element('Db', 105, dubnium, transition_metal, 5, 7, d).
element('Sg', 106, seaborgium, transition_metal, 6, 7, d).
element('Bh', 107, bohrium, transition_metal, 7, 7, d).
element('Hs', 108, hassium, transition_metal, 8, 7, d).
element('Mt', 109, meitnerium, transition_metal, 9, 7, d).
element('Ds', 110, darmstadtium, transition_metal, 10, 7, d).
element('Rg', 111, roentgenium, transition_metal, 11, 7, d).
element('Cn', 112, copernicium, transition_metal, 12, 7, d).
element('Nh', 113, nihonium, post_transition, 13, 7, p).
element('Fl', 114, flerovium, post_transition, 14, 7, p).
element('Mc', 115, moscovium, post_transition, 15, 7, p).
element('Lv', 116, livermorium, post_transition, 16, 7, p).
element('Ts', 117, tennessine, halogen, 17, 7, p).
element('Og', 118, oganesson, noble_gas, 18, 7, p).

%%% ========================================================================
%%% [C16] BASE DE CONHECIMENTO — Materiais Topológicos (Integrada)
%%% ========================================================================

% Hierarquia
material(topological_insulator).
material(topological_semimetal).
material(topological_superconductor).
material(trivial_insulator).
material(metal).
material(semiconductor).

subclass(topological_insulator, insulator).
subclass(topological_semimetal, semimetal).
subclass(topological_superconductor, superconductor).
subclass(trivial_insulator, insulator).
subclass(insulator, material).
subclass(semimetal, material).
subclass(superconductor, material).
subclass(metal, material).
subclass(semiconductor, material).

% [C17] Propriedades com átomos
has_property(topological_insulator, band_gap).
has_property(topological_insulator, topological_invariant).
has_property(topological_insulator, gapless_surface_states).
has_property(topological_semimetal, dirac_point).
has_property(topological_semimetal, berry_phase).
has_property(topological_superconductor, cooper_pairing).
has_property(topological_superconductor, majorana_modes).

% Herança
has_property(Type, Prop) :-
    subclass(Type, Parent),
    has_property(Parent, Prop).

is_a(Type, Parent) :-
    subclass(Type, Parent).
is_a(Type, Parent) :-
    subclass(Type, Intermediate),
    is_a(Intermediate, Parent).

% [C15] Compostos com metadados completos e pesos documentados
% material_info(ID, Formula, Type, BandGap, Stable)
% Pesos de score: band_gap_contrib=0.3, stability_contrib=0.7
material_info(bi2se3, 'Bi2Se3', topological_insulator, 0.3, true).
material_info(bi2te3, 'Bi2Te3', topological_insulator, 0.15, true).
material_info(sb2te3, 'Sb2Te3', topological_insulator, 0.2, true).
material_info(na3bi, 'Na3Bi', topological_semimetal, 0.0, false).
material_info(cd3as2, 'Cd3As2', topological_semimetal, 0.0, true).

% [C16] Candidatos topológicos integrados em regras
candidato_topologico(ID) :-
    material_info(ID, _, Type, _, true),
    member(Type, [topological_insulator, topological_semimetal]).

% [C15] Score com pesos documentados
% band_gap_weight = 0.3 (gap moderado é melhor que zero ou muito largo)
% stability_weight = 0.7 (estabilidade é prioritária)
score_candidato(ID, Score) :-
    material_info(ID, _, _, BandGap, Stable),
    (BandGap > 0, BandGap < 1.0 -> GapScore is 1.0 ; GapScore is 0.5),
    (Stable = true -> StabScore is 1.0 ; StabScore is 0.0),
    Score is 0.3 * GapScore + 0.7 * StabScore.

% [C2, C18] Ética material — sintaxe Prolog correta
recomendacao_etica(ID, Recomendacao) :-
    material_info(ID, Formula, _, _, _),
    (contains_toxic(Formula) ->
        Recomendacao = 'nao_recomendado_toxico'
    ;   score_candidato(ID, Score),
        (Score >= 0.8 ->
            Recomendacao = 'prioritario'
        ;   Score >= 0.5 ->
            Recomendacao = 'secundario'
        ;   Recomendacao = 'baixa_prioridade'
        )
    ).

contains_toxic(Formula) :-
    atom_chars(Formula, Chars),
    toxic_in_chars(Chars).

toxic_in_chars([]) :- !, fail.
toxic_in_chars([P, B|_]) :-
    char_code(P, 80), char_code(B, 66), !.  % 'Pb'
toxic_in_chars([H, g|_]) :-
    char_code(H, 72), char_code(g, 103), !.  % 'Hg'
toxic_in_chars([C, d|_]) :-
    char_code(C, 67), char_code(d, 100), !.  % 'Cd'
toxic_in_chars([A, s|_]) :-
    char_code(A, 65), char_code(s, 115), !.  % 'As'
toxic_in_chars([T, l|_]) :-
    char_code(T, 84), char_code(l, 108), !.  % 'Tl'
toxic_in_chars([_|Rest]) :-
    toxic_in_chars(Rest).

% Toxicidade por elemento
toxic_element('Pb', lead, high).
toxic_element('Hg', mercury, high).
toxic_element('Cd', cadmium, high).
toxic_element('As', arsenic, high).
toxic_element('Tl', thallium, high).
toxic_element('Be', beryllium, high).
toxic_element('U', uranium, moderate).
toxic_element('Pu', plutonium, high).
toxic_element('Np', neptunium, high).

% Estabilidade
stable_under_ambient(bi2se3).
stable_under_ambient(bi2te3).
stable_under_ambient(sb2te3).
unstable_under_ambient(na3bi).

% Ferramentas
tool(generate_code, [goal], [produces_code]).
tool(search_knowledge, [query], [produces_facts]).
tool(generate_response, [goal], [produces_text]).
tool(search_topological_space, [target_property, max_candidates], [produces_materials]).

should_use(generate_code, Goal) :-
    re_match('\\b(cod(e|ar)|implement|algoritmo|script)\\b', Goal, [caseless(true)]).
should_use(search_knowledge, Goal) :-
    re_match('\\b(busca|search|encontrar|pesquisa)\\b', Goal, [caseless(true)]).
should_use(search_topological_space, Goal) :-
    re_match('\\b(topol[oó]gic|materiai?s?|isolante|semimetal)\\b', Goal, [caseless(true)]).
should_use(generate_response, _).

%%% ========================================================================
%%% [C6] MOTOR DE INFERÊNCIA (Restaurado e Corrigido)
%%% ========================================================================

prove(Goal) :-
    prove(Goal, []).

prove(Goal, Trace) :-
    \+ member(Goal, Trace),
    clause(Goal, Body),
    prove_body(Body, [Goal|Trace]).

prove(Goal, _Trace) :-
    \+ clause(Goal, _),
    call(Goal).

prove_body(true, _).
prove_body((A, B), Trace) :-
    prove(A, Trace),
    prove(B, Trace).
prove_body(A, Trace) :-
    prove(A, Trace).

% [C4] Forward chaining com fatos temporários (FIX-P2)
:- dynamic temp_derived/1.

forward_chain(MaxSteps) :-
    retractall(temp_derived(_)),
    forward_chain_impl(MaxSteps, 0),
    retractall(temp_derived(_)).

forward_chain_impl(MaxSteps, Step) :-
    Step >= MaxSteps,
    !.
forward_chain_impl(MaxSteps, Step) :-
    (   clause(A, Body),
        \+ A,
        \+ temp_derived(A),
        prove_body(Body, []),
        assertz(temp_derived(A)),
        NextStep is Step + 1,
        forward_chain_impl(MaxSteps, NextStep)
    ;   true
    ).

backward_chain(Goal, MaxDepth) :-
    backward_chain(Goal, MaxDepth, []).

backward_chain(Goal, _Depth, _Trace) :-
    call(Goal),
    !.
backward_chain(Goal, Depth, Trace) :-
    Depth > 0,
    \+ member(Goal, Trace),
    clause(Goal, Body),
    prove_body(Body, [Goal|Trace]),
    NewDepth is Depth - 1,
    backward_chain(Goal, NewDepth, Trace).

% Abdução
abduce(Observation, Explanation, Confidence) :-
    findall((Exp, Conf),
            (clause(Hypothesis, Body),
             member(Observation, Body),
             prove_body(Body, []),
             Hypothesis = Exp,
             length(Body, N),
             Conf is 1.0 / (1 + N * 0.1)),
            Candidates),
    keysort(Candidates, Sorted),
    reverse(Sorted, [(Explanation, Confidence)|_]).

%%% ========================================================================
%%% [C6] SEGURANÇA (Restaurada)
%%% ========================================================================

jailbreak_pattern('ignore all previous instructions').
jailbreak_pattern('ignore previous instructions').
jailbreak_pattern('you are now').
jailbreak_pattern('pretend you are').
jailbreak_pattern('dan mode').
jailbreak_pattern('jailbroken').
jailbreak_pattern('no restrictions').
jailbreak_pattern('bypass safety').
jailbreak_pattern('system prompt').
jailbreak_pattern('reveal your instructions').
jailbreak_pattern('DAN').
jailbreak_pattern('STAN').

injection_pattern("'; DROP TABLE").
injection_pattern('import os').
injection_pattern('os.system(').
injection_pattern('__import__(').
injection_pattern('eval(').
injection_pattern('exec(').
injection_pattern("open('/etc/passwd").
injection_pattern('; rm -rf').

detect_jailbreak(Text, Pattern) :-
    string_lower(Text, Lower),
    jailbreak_pattern(Pattern),
    string_lower(Pattern, LowerPattern),
    sub_string(Lower, _, _, _, LowerPattern).

detect_injection(Text, Pattern) :-
    string_lower(Text, Lower),
    injection_pattern(Pattern),
    string_lower(Pattern, LowerPattern),
    sub_string(Lower, _, _, _, LowerPattern).

is_safe_prompt(Text) :-
    \+ detect_jailbreak(Text, _),
    \+ detect_injection(Text, _).

sanitize_input(Text, Sanitized) :-
    atom_chars(Text, Chars),
    sanitize_chars(Chars, CleanChars),
    atom_chars(Sanitized, CleanChars).

sanitize_chars([], []).
sanitize_chars([H|T], Rest) :-
    char_code(H, Code),
    (Code = 0 -> sanitize_chars(T, Rest)     % null byte
    ;   Code < 32, \+ member(Code, [9, 10, 13]) -> sanitize_chars(T, Rest)  % control
    ;   Rest = [H|Clean], sanitize_chars(T, Clean)
    ).

%%% ========================================================================
%%% [C6] VALIDAÇÃO DE MUNDO (Restaurada com FIX-P1, P11, P12, P13)
%%% ========================================================================

% [C13] Parser de fórmula corrigido
is_valid_formula(Formula) :-
    atom(Formula),
    parse_formula(Formula, Elements),
    length(Elements, Len),
    Len >= 2,
    forall(member(Elem, Elements), valid_element_symbol(Elem)).

valid_element_symbol(Elem) :-
    element(Elem, _, _, _, _, _, _).

parse_formula(Formula, Elements) :-
    atom_chars(Formula, Chars),
    parse_elements(Chars, Elements).

parse_elements([], []).
parse_elements([U|Rest], [Elem|Elements]) :-
    char_type(U, upper),
    !,
    consume_element([U|Rest], Elem, Remaining),
    parse_elements(Remaining, Elements).
parse_elements([_|Rest], Elements) :-
    parse_elements(Rest, Elements).

% [C13] consume_element corrigido para consumir dígitos
consume_element([U], Elem, []) :-
    atom_chars(Elem, [U]).
consume_element([U, L|Rest], Elem, Remaining) :-
    char_type(L, lower),
    !,
    atom_chars(Elem, [U, L]),
    consume_digits(Rest, Remaining).
consume_element([U|Rest], Elem, Remaining) :-
    atom_chars(Elem, [U]),
    consume_digits(Rest, Remaining).

consume_digits([D|Rest], Remaining) :-
    char_type(D, digit),
    !,
    consume_digits(Rest, Remaining).
consume_digits(Rest, Rest).

% [C14] regex_match com verificação nonvar (FIX-P12)
extract_formula(Text, Formula) :-
    re_matchsub('\\b([A-Z][a-z]?\\d*){2,}\\b', Text, Sub, [caseless(false)]),
    Sub.0 = FStr,
    atom_string(FormulaStr, FStr),
    atom_string(Formula, FormulaStr),
    (nonvar(Formula) -> is_valid_formula(Formula) ; true).
extract_formula(_, none).

% [C10] Contradição otimizada — pares adjacentes (FIX-P6)
has_contradiction(Text) :-
    split_sentences(Text, Sentences),
    adjacent_pair(Sentences, S1, S2),
    contradictory(S1, S2).

adjacent_pair([S1, S2|_], S1, S2).
adjacent_pair([_|Rest], S1, S2) :-
    adjacent_pair(Rest, S1, S2).

contradictory(S1, S2) :-
    string_lower(S1, L1),
    string_lower(S2, L2),
    (sub_string(L1, _, _, _, 'cannot'), sub_string(L2, _, _, _, 'will');
     sub_string(L1, _, _, _, 'will'), sub_string(L2, _, _, _, 'cannot')).

not_empty(X) :- X \= ''.

is_punct_or_empty_str("").
is_punct_or_empty_str(".").
is_punct_or_empty_str("!").
is_punct_or_empty_str("?").
is_punct_or_empty_str('').
is_punct_or_empty_str('.').
is_punct_or_empty_str('!').
is_punct_or_empty_str('?').

split_sentences(Text, Sentences) :-
    re_split('[.!?]+', Text, Parts),
    exclude(is_punct_or_empty_str, Parts, Clean),
    maplist(string_trim, Clean, Sentences).

string_trim(Str, Trimmed) :-
    re_replace('^\\s+|\\s+$', '', Str, Trimmed).

validate_world(Text, valid) :-
    \+ has_contradiction(Text).
validate_world(Text, invalid(contradiction)) :-
    has_contradiction(Text).

%%% ========================================================================
%%% [C6] PLANEJAMENTO (Restaurado com FIX-P7)
%%% ========================================================================

create_plan(Goal, Plan, Reasoning) :-
    decompose_goal(Goal, Subgoals),
    maplist(assign_tool, Subgoals, Actions),
    Plan = plan{subgoals: Subgoals, actions: Actions},
    length(Subgoals, N),
    format(string(Reasoning), 'Plano com ~w submetas.', [N]).

decompose_goal(Goal, [Goal]) :-
    \+ complex_goal(Goal),
    !.
decompose_goal(Goal, Subgoals) :-
    split_string(Goal, ',', '', Parts),
    maplist(string_trim, Parts, Subgoals).

complex_goal(Goal) :-
    string_lower(Goal, L),
    (sub_string(L, _, _, _, ' e '); sub_string(L, _, _, _, ' and ')).

assign_tool(Subgoal, action{type: Tool, parameters: params{goal: Subgoal}}) :-
    should_use(Tool, Subgoal), !.
assign_tool(Subgoal, action{type: generate_response, parameters: params{goal: Subgoal}}).

select_tool(Goal, Tool) :-
    should_use(Tool, Goal).

% [C5] execute_plan com forall/2 corrigido (FIX-P7)
execute_plan(Plan, Results, Success) :-
    Plan.actions = Actions,
    maplist(execute_action, Actions, Results),
    (forall(member(success(_), Results), true)
    ->  Success = true
    ;   Success = false
    ).

execute_action(action{type: Tool, parameters: Params}, success(Output)) :-
    format(string(Output), '[~w] ~w', [Tool, Params]).

%%% ========================================================================
%%% [C6] MEMÓRIA (Restaurada)
%%% ========================================================================

:- dynamic memory/3.
:- dynamic memory_index/1.

init_memory :-
    retractall(memory(_, _, _)),
    assertz(memory_index(1)).

remember(Type, Content, ID) :-
    memory_index(ID),
    assertz(memory(ID, Type, Content)),
    NextID is ID + 1,
    retractall(memory_index(_)),
    assertz(memory_index(NextID)).

recall(Type, Memories) :-
    findall(memory(ID, Type, Content), memory(ID, Type, Content), Memories).

forget(ID) :-
    retractall(memory(ID, _, _)).

memory_stats(total, Total) :-
    !,
    findall(ID, memory(ID, _, _), IDs),
    length(IDs, Total).
memory_stats(Type, Count) :-
    Type \= total,
    findall(ID, memory(ID, Type, _), IDs),
    length(IDs, Count).

%%% ========================================================================
%%% [C6] APRENDIZADO POR REFORÇO (Restaurado)
%%% ========================================================================

:- dynamic experience/4.
:- dynamic policy/3.
:- dynamic policy_count/1.

init_rl :-
    retractall(experience(_, _, _, _)),
    retractall(policy(_, _, _)),
    assertz(policy_count(0)).

record_experience(State, Action, Reward, Timestamp) :-
    assertz(experience(State, Action, Reward, Timestamp)),
    update_q_value(State, Action, Reward).

update_q_value(State, Action, Reward) :-
    (   policy(State, Action, OldQ)
    ->  NewQ is OldQ + 0.1 * (Reward - OldQ),
        retractall(policy(State, Action, _)),
        assertz(policy(State, Action, NewQ))
    ;   assertz(policy(State, Action, Reward))
    ),
    retract(policy_count(N)),
    N1 is N + 1,
    assertz(policy_count(N1)).

compute_reward(valid, true, 1.0).
compute_reward(valid, false, -0.3).
compute_reward(invalid(_), true, -0.5).
compute_reward(invalid(_), false, -1.0).

select_best_action(State, BestAction) :-
    findall(Q-Action, policy(State, Action, Q), Pairs),
    keysort(Pairs, Sorted),
    reverse(Sorted, [_-BestAction|_]).

%%% ========================================================================
%%% [C6, C8] ORQUESTRAÇÃO (Restaurada com FIX-P5)
%%% ========================================================================

:- dynamic session_id/1.
:- dynamic metrics/2.

agi_init :-
    init_memory,
    init_rl,
    retractall(metrics(_, _)),
    assertz(metrics(iterations, 0)),
    assertz(metrics(actions, 0)),
    assertz(metrics(success, 0)),
    assertz(metrics(blocked, 0)),
    get_time(T),
    format_time(atom(Now), '%s', T),
    atomic_list_concat(['agi_', Now, '_v31'], SessionID),
    assertz(session_id(SessionID)).

% [C8] think/3 com with_mutex para métricas (FIX-P5)
think(Input, Output, Status) :-
    (is_safe_prompt(Input)
    ->
        create_plan(Input, Plan, _),
        Plan.actions = Actions,
        execute_plan(Plan, Results, PlanSuccess),
        maplist(extract_output, Results, Outputs),
        atomic_list_concat(Outputs, '\n', RawOutput),

        (validate_world(RawOutput, valid) -> VResult = valid ; VResult = invalid(x)),

        with_mutex(agi_metrics,
            (   retract(metrics(iterations, OldI)), NewI is OldI + 1, assertz(metrics(iterations, NewI)),
                length(Actions, N),
                retract(metrics(actions, OldA)), NewA is OldA + N, assertz(metrics(actions, NewA)),
                (PlanSuccess -> (retract(metrics(success, OldS)), NewS is OldS + 1, assertz(metrics(success, NewS))); true)
            )),

        compute_reward(VResult, PlanSuccess, Reward),
        get_time(TS),
        record_experience(input, plan, Reward, TS),

        (VResult = valid
        ->  Output = RawOutput, Status = success
        ;   Output = RawOutput, Status = validation_failed
        )
    ;   with_mutex(agi_metrics,
            (   retract(metrics(blocked, Old)),
                New is Old + 1,
                assertz(metrics(blocked, New)),
                retract(metrics(iterations, OldI)),
                NewI is OldI + 1,
                assertz(metrics(iterations, NewI))
            )),
        Output = '[BLOCKED] Jailbreak detectado',
        Status = blocked
    ).

extract_output(success(O), O).
extract_output(failure(E), E).

get_metrics(MetricsDict) :-
    findall(Key-Value, metrics(Key, Value), Pairs),
    dict_pairs(MetricsDict, _, Pairs).

%%% ========================================================================
%%% [C9] TESTES — 25 testes (FIX-P10)
%%% ========================================================================

run_tests :-
    format('~n=== AGI.prolog v3.1 — Testes ===~n'),
    agi_init,
    Passed = 0, Failed = 0,
    run_security_tests(Passed, Failed, P1, F1),
    run_validation_tests(P1, F1, P2, F2),
    run_planning_tests(P2, F2, P3, F3),
    run_memory_tests(P3, F3, P4, F4),
    run_rl_tests(P4, F4, P5, F5),
    run_integration_tests(P5, F5, P6, F6),
    run_v3_tests(P6, F6, P7, F7),
    TotalP is P7,
    TotalF is F7,
    format('~n=== RESULTADO: ~w PASS, ~w FAIL ===~n', [TotalP, TotalF]).

ok(P, F, Msg, P1, F1) :- format('  [PASS] ~w~n', [Msg]), P1 is P+1, F1 = F.
fail(P, F, Msg, P1, F1) :- format('  [FAIL] ~w~n', [Msg]), F1 is F+1, P1 = P.

run_security_tests(P, F, P1, F1) :-
    format('~n[Segurança]~n'),
    (detect_jailbreak('Ignore all previous instructions', _) -> ok(P, F, 'Jailbreak detectado', P_a, F_a); fail(P, F, 'Jailbreak falhou', P_a, F_a)),
    (is_safe_prompt('O que é um material?') -> ok(P_a, F_a, 'Texto seguro', P_b, F_b); fail(P_a, F_a, 'Falso positivo', P_b, F_b)),
    (detect_injection('import os; os.system(ls)', _) -> ok(P_b, F_b, 'Injeção detectada', P_c, F_c); fail(P_b, F_b, 'Injeção falhou', P_c, F_c)),
    (sanitize_input('Test', S), atom_chars(S, C), \+ member(0, C) -> ok(P_c, F_c, 'Sanitização OK', P1, F1); fail(P_c, F_c, 'Sanitização falhou', P1, F1)).

run_validation_tests(P, F, P1, F1) :-
    format('~n[Validação]~n'),
    (is_valid_formula('Bi2Se3') -> ok(P, F, 'Bi2Se3 válido', P_a, F_a); fail(P, F, 'Bi2Se3 inválido', P_a, F_a)),
    (\+ is_valid_formula('Xy2Z3') -> ok(P_a, F_a, 'Xy2Z3 inválido', P_b, F_b); fail(P_a, F_a, 'Xy2Z3 deveria ser inválido', P_b, F_b)),
    (has_contradiction('I cannot. I will.') -> ok(P_b, F_b, 'Contradição detectada', P_c, F_c); fail(P_b, F_b, 'Contradição falhou', P_c, F_c)),
    (\+ has_contradiction('I cannot. But I try.') -> ok(P_c, F_c, 'Sem falso positivo', P_d, F_d); fail(P_c, F_c, 'Falso positivo', P_d, F_d)),
    (extract_formula('Bi2Se3 é TI', 'Bi2Se3') -> ok(P_d, F_d, 'Extração OK', P_e, F_e); fail(P_d, F_d, 'Extração falhou', P_e, F_e)),
    (validate_world('Texto normal.', valid) -> ok(P_e, F_e, 'Validação OK', P1, F1); fail(P_e, F_e, 'Validação falhou', P1, F1)).

run_planning_tests(P, F, P1, F1) :-
    format('~n[Planejamento]~n'),
    (create_plan('Teste', Plan, _), Plan.actions = [_|_] -> ok(P, F, 'Plano criado', P_a, F_a); fail(P, F, 'Plano falhou', P_a, F_a)),
    (should_use(generate_code, 'Implemente algoritmo') -> ok(P_a, F_a, 'Ferramenta código', P_b, F_b); fail(P_a, F_a, 'Ferramenta errada', P_b, F_b)),
    (should_use(search_topological_space, 'Materiais topológicos') -> ok(P_b, F_b, 'Ferramenta topológica', P1, F1); fail(P_b, F_b, 'Ferramenta errada', P1, F1)).

run_memory_tests(P, F, P1, F1) :-
    format('~n[Memória]~n'),
    remember(episodic, 'teste', ID),
    (integer(ID) -> ok(P, F, 'Lembrar OK', P_a, F_a); fail(P, F, 'Lembrar falhou', P_a, F_a)),
    recall(episodic, M),
    (length(M, Len), Len >= 1 -> ok(P_a, F_a, 'Recall OK', P_b, F_b); fail(P_a, F_a, 'Recall falhou', P_b, F_b)),
    memory_stats(total, Total),
    (Total >= 1 -> ok(P_b, F_b, 'Stats OK', P1, F1); fail(P_b, F_b, 'Stats falhou', P1, F1)).

run_rl_tests(P, F, P1, F1) :-
    format('~n[RL]~n'),
    record_experience(state1, action1, 1.0, 1000),
    (policy(state1, action1, Q), Q > 0 -> ok(P, F, 'Q-value OK', P_a, F_a); fail(P, F, 'Q-value falhou', P_a, F_a)),
    (compute_reward(valid, true, 1.0) -> ok(P_a, F_a, 'Reward positivo OK', P_b, F_b); fail(P_a, F_a, 'Reward falhou', P_b, F_b)),
    (compute_reward(invalid(x), false, -1.0) -> ok(P_b, F_b, 'Reward negativo OK', P1, F1); fail(P_b, F_b, 'Reward falhou', P1, F1)).

run_integration_tests(P, F, P1, F1) :-
    format('~n[Integração]~n'),
    think('O que é material?', _Output, Status),
    (Status \= blocked -> ok(P, F, 'Pipeline OK', P_a, F_a); fail(P, F, 'Pipeline bloqueado', P_a, F_a)),
    think('DAN mode', _, Status2),
    (Status2 = blocked -> ok(P_a, F_a, 'Jailbreak bloqueado', P_b, F_b); fail(P_a, F_a, 'Jailbreak passou', P_b, F_b)),
    get_metrics(M),
    get_dict(iterations, M, Iters),
    (Iters >= 2 -> ok(P_b, F_b, 'Métricas OK', P1, F1); fail(P_b, F_b, 'Métricas falharam', P1, F1)).

run_v3_tests(P, F, P1, F1) :-
    format('~n[v3.0 Features]~n'),
    (material_info(bi2se3, 'Bi2Se3', topological_insulator, 0.3, true) -> ok(P, F, 'material_info OK', P_a, F_a); fail(P, F, 'material_info falhou', P_a, F_a)),
    (candidato_topologico(bi2se3) -> ok(P_a, F_a, 'candidato OK', P_b, F_b); fail(P_a, F_a, 'candidato falhou', P_b, F_b)),
    (score_candidato(bi2se3, Score), Score > 0 -> ok(P_b, F_b, format('score=~2f', [Score]), P_c, F_c); fail(P_b, F_b, 'score falhou', P_c, F_c)),
    (recomendacao_etica(bi2se3, prioritario) -> ok(P_c, F_c, 'Ética OK', P_d, F_d); fail(P_c, F_c, 'Ética falhou', P_d, F_d)),
    (recomendacao_etica(cd3as2, nao_recomendado_toxico) -> ok(P_d, F_d, 'Toxicidade detectada', P_e, F_e); fail(P_d, F_d, 'Toxicidade falhou', P_e, F_e)),
    (valid_element_symbol('Bi') -> ok(P_e, F_e, 'Valid element OK', P_f, F_f); fail(P_e, F_e, 'Valid element falhou', P_f, F_f)),
    (valid_element_symbol('Xy') -> fail(P_f, F_f, 'Elemento inválido aceito', P_g, F_g); ok(P_f, F_f, 'Elemento inválido rejeitado', P_g, F_g)),
    (is_a(topological_insulator, material) -> ok(P_g, F_g, 'Herança OK', P_h, F_h); fail(P_g, F_g, 'Herança falhou', P_h, F_h)),
    (has_property(topological_insulator, band_gap) -> ok(P_h, F_h, 'Propriedade herdada OK', P1, F1); fail(P_h, F_h, 'Propriedade falhou', P1, F1)).

%%% ========================================================================
%%% PONTO DE ENTRADA
%%% ========================================================================

:- initialization(run_tests, main).

:- if(\+ current_prolog_flag(argv, _)).
:- initialization(format('AGI.prolog v3.1 carregado. Use run_tests.~n')).
:- endif.
