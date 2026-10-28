import streamlit as st
import pandas as pd
import json
from datetime import datetime

st.set_page_config(
    page_title="CoachMe Universal Diagnostic Tool",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header { font-family: Arial, sans-serif; color: #1E3A8A; font-weight: 800; }
    .sub-header { color: #4B5563; font-size: 1.1rem; margin-bottom: 25px; }
    .kpi-card { background-color: #F3F4F6; border-left: 5px solid #2563EB; padding: 18px; border-radius: 8px; margin-bottom: 15px; }
    .kpi-title { font-size: 0.85rem; text-transform: uppercase; color: #6B7280; font-weight: 700; }
    .kpi-value { font-size: 1.8rem; font-weight: 800; color: #1F2937; }
    .kpi-desc { font-size: 0.9rem; color: #4B5563; margin-top: 5px; }
    .cva-box-high { background-color: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 8px; padding: 12px; margin-bottom: 10px; }
    .cva-box-mid { background-color: #F3F4F6; border: 1px solid #E5E7EB; border-radius: 8px; padding: 12px; margin-bottom: 10px; }
    .cva-box-low { background-color: #FEF2F2; border: 1px solid #FCA5A5; border-radius: 8px; padding: 12px; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

CVA_INFO = {
    1: {
        "name": "Societal Change",
        "tagline": "Influencing Opinions",
        "description": "Driven to make a broad difference, address systemic issues, effect policy change, and advocate for the common good.",
        "key_traits": ["Strong, confident communicator", "Passionate about justice & rights", "Influential & persuasive"],
        "caution_areas": ["Could be highly judgmental of differing views", "May push change too aggressively", "Risk of institutional friction"]
    },
    2: {
        "name": "Theoretical Discovery",
        "tagline": "Answering Questions",
        "description": "Focused on research, intellectual rigor, root cause investigation, data synthesis, and technical mastery.",
        "key_traits": ["Analytically rigorous", "Deep investigator & problem-solver", "Objective & truth-seeking"],
        "caution_areas": ["Might over-analyze and delay decisions", "Can appear detached or overly clinical", "Risk of excessive worrying over details"]
    },
    3: {
        "name": "Strategic Decisions",
        "tagline": "Managing Plans",
        "description": "Oriented around long-range planning, organizational control, resource optimization, and strategic alignment.",
        "key_traits": ["Methodical planner", "Clear decision-maker", "Focuses on strategic alignment"],
        "caution_areas": ["May become overly controlling", "Reluctant to delegate critical tasks", "Frustrated by ambiguity or lack of structure"]
    },
    4: {
        "name": "Human Development",
        "tagline": "Helping People",
        "description": "Committed to nurturing individual potential, providing pastoral/relational care, coaching, and personal growth.",
        "key_traits": ["Deeply empathetic & caring", "Unlocks human potential", "Protects individual dignity"],
        "caution_areas": ["The Messiah Trap (over-protecting others)", "Tendency to take criticism personally", "Difficulty setting tough boundaries"]
    },
    5: {
        "name": "Entrepreneurial Challenge",
        "tagline": "Taking Risks",
        "description": "Energized by pioneering new initiatives, taking calculated risks, embracing competition, and overcoming obstacles.",
        "key_traits": ["Bold & adventurous", "Pioneers new opportunities", "Resilient under uncertainty"],
        "caution_areas": ["May take unnecessary risks", "Impatience with routine operations", "Can become overly competitive"]
    },
    6: {
        "name": "Production Efficiency",
        "tagline": "Maintaining Order",
        "description": "Dedicated to process integrity, operational execution, maintaining standards, and structured order.",
        "key_traits": ["Reliable & process-driven", "High operational standards", "Ensures execution & order"],
        "caution_areas": ["Rigidity against needed innovation", "Frustrated by procedural delays", "Perfectionism that slows progress"]
    },
    7: {
        "name": "Artistic Creativity",
        "tagline": "Designing Innovations",
        "description": "Inspired by aesthetics, creative expression, original design, storytelling, and novel visual/conceptual solutions.",
        "key_traits": ["Highly imaginative & original", "Aesthetic sensibility", "Expresses ideas creatively"],
        "caution_areas": ["Frustration when forced into rigid routines", "May insist on own creative vision", "Can hold on to criticism deeply"]
    },
    8: {
        "name": "Natural Appreciation",
        "tagline": "Keeping Balance",
        "description": "Observant and balanced; connects disparate dots, values harmony, respects creation, and maintains holistic perspective.",
        "key_traits": ["Holistic dot-connector", "Observant & discerning", "Promotes balance & environmental harmony"],
        "caution_areas": ["May appear aloof or overly quiet under stress", "Defensive walls when values are crossed", "Grudges against disrespectful behavior"]
    },
    9: {
        "name": "Motivational Energy",
        "tagline": "Energizing Others",
        "description": "Commands dynamic energy, inspires enthusiasm, catalyzes action, and brings joy and vitality to groups.",
        "key_traits": ["Infectiously enthusiastic", "Inspires & mobilizes teams", "Creates engaging environments"],
        "caution_areas": ["Might tend to talk too much or dominate space", "Can overwhelm quieter team members", "May rely on charisma over detail"]
    }
}

MODEL_ROLE_RULES = [
    {
        "roles": ["Advocate", "Defender", "Culturalist"],
        "trigger": lambda top_set: {1, 4}.issubset(top_set) or {1, 8}.issubset(top_set) or {4, 8}.issubset(top_set),
        "descriptions": {
            "Advocate": "One who argues and pleads for others in support of an issue, cause, or marginalized community.",
            "Defender": "One who protects the defenseless or vulnerable from harm, building sanctuary and safety.",
            "Culturalist": "One who works to preserve, interpret, and shape healthy cultural patterns and societal institutions."
        }
    },
    {
        "roles": ["Motivator", "Educator", "Public Service Facilitator"],
        "trigger": lambda top_set: {4, 9}.issubset(top_set) or {1, 9}.issubset(top_set),
        "descriptions": {
            "Motivator": "One who inspires others to action through enthusiasm and clear purpose.",
            "Educator": "One who imparts knowledge, wisdom, and practical skills to help others grow.",
            "Public Service Facilitator": "One who uses commitment and energy to motivate and improve community well-being."
        }
    },
    {
        "roles": ["Researcher", "Administrator", "Technologist"],
        "trigger": lambda top_set: {2, 3}.issubset(top_set) or {2, 6}.issubset(top_set) or {3, 6}.issubset(top_set),
        "descriptions": {
            "Researcher": "One who systematically investigates root causes, data, and deep explanations.",
            "Administrator": "One who runs, organizes, and maintains smooth operational functions and projects.",
            "Technologist": "One who applies analytical methods and technical tools to solve complex challenges."
        }
    },
    {
        "roles": ["Market Leader", "Spokesperson", "Persuader"],
        "trigger": lambda top_set: {5, 9}.issubset(top_set) or {5, 3}.issubset(top_set) or {1, 5}.issubset(top_set),
        "descriptions": {
            "Market Leader": "A charismatic leader who gathers people and resources to achieve bold objectives.",
            "Spokesperson": "One who articulates key messages and represents an organization or cause publicly.",
            "Persuader": "One who modifies and positively impacts the thoughts and behaviors of others."
        }
    },
    {
        "roles": ["Health & Welfare Minister", "Supporter", "Counselor"],
        "trigger": lambda top_set: {4, 8}.issubset(top_set) or {4, 6}.issubset(top_set),
        "descriptions": {
            "Health & Welfare Minister": "One who serves through practical empathy, tangible care, and restorative action.",
            "Supporter": "One who promotes, encourages, and advocates for another person's growth and ideas.",
            "Counselor": "One who listens deeply and guides others toward personal effectiveness and peace."
        }
    },
    {
        "roles": ["Cultural Design Expert", "Originator", "Creative Consultant"],
        "trigger": lambda top_set: 7 in top_set,
        "descriptions": {
            "Cultural Design Expert": "One who understands cultural nuances and designs unique visual or narrative solutions.",
            "Originator": "One who invents or creates novel, groundbreaking concepts from scratch.",
            "Creative Consultant": "One who guides teams using artistic vision, storytelling, and fresh design perspectives."
        }
    }
]

DEFAULT_MODEL_ROLES = {
    "Facilitator": "One who helps others achieve goals efficiently, harmoniously, and effectively.",
    "Organizer": "One who puts ideas, resources, and people together into an orderly, functional structure.",
    "Advisor": "One who offers wisdom, objective perspective, and guidance based on experience."
}

QUESTIONS = [
    {
        "id": "q1",
        "dimension": "Mission",
        "text": "What type of challenge excites you the most on a Monday morning?",
        "options": [
            ("Advocating for a social cause or making a broad societal impact", 1),
            ("Investigating a complex question or solving an intellectual puzzle", 2),
            ("Developing a long-term strategic plan or organizational system", 3),
            ("Coaching an individual or helping someone overcome a personal hurdle", 4)
        ]
    },
    {
        "id": "q2",
        "dimension": "Mission",
        "text": "When choosing a project to lead or join, what matters most to you?",
        "options": [
            ("Pioneering a bold new initiative with high risk and high reward", 5),
            ("Building an efficient, reliable process that runs smoothly", 6),
            ("Creating something beautifully designed, creative, or artistic", 7),
            ("Connecting different dots, observing, and maintaining holistic balance", 8)
        ]
    },
    {
        "id": "q3",
        "dimension": "Mission",
        "text": "Where do you feel your personal battery most naturally recharged?",
        "options": [
            ("Energizing a group, speaking publicly, or inspiring enthusiasm", 9),
            ("Working directly with individuals to support their growth and development", 4),
            ("Challenging the status quo and influencing public opinion", 1),
            ("Analyzing data, conducting research, and discovering objective truths", 2)
        ]
    },
    {
        "id": "q4",
        "dimension": "Competency",
        "text": "Which of these tasks comes most naturally and effortlessly to you?",
        "options": [
            ("Organizing schedules, logistics, and procedural workflows", 6),
            ("Designing unique visual concepts, stories, or creative works", 7),
            ("Quietly observing complex situations and seeing how elements connect", 8),
            ("Rallying people around a shared vision and generating excitement", 9)
        ]
    },
    {
        "id": "q5",
        "dimension": "Competency",
        "text": "If a critical problem arises in your team, what is your go-to strength?",
        "options": [
            ("Taking charge and establishing a clear strategic roadmap", 3),
            ("Listening deeply and providing empathetic guidance to those affected", 4),
            ("Taking calculated risks and experimenting with bold solutions", 5),
            ("Digging into data to diagnose the underlying root cause", 2)
        ]
    },
    {
        "id": "q6",
        "dimension": "Competency",
        "text": "What do colleagues or friends most often praise you for?",
        "options": [
            ("Your ability to stand up for what's right and advocate for others", 1),
            ("Your ability to make sense of complex information and answer tough questions", 2),
            ("Your knack for structuring chaotic projects into orderly execution", 6),
            ("Your ability to create a warm, inspiring, and energizing environment", 9)
        ]
    },
    {
        "id": "q7",
        "dimension": "Style",
        "text": "How do others observe you behaving in team settings?",
        "options": [
            ("Passionate, vocal, and willing to challenge established rules", 1),
            ("Thoughtful, detail-oriented, and focused on accuracy", 2),
            ("Strategic, organized, and focused on milestones", 3),
            ("Warm, encouraging, and focused on personal well-being", 4)
        ]
    },
    {
        "id": "q8",
        "dimension": "Style",
        "text": "Under pressure or stress, what behavioral tendency do you notice in yourself?",
        "options": [
            ("Pushing hard for quick results and taking swift, decisive risks", 5),
            ("Insisting strictly on rules, quality standards, and correct procedures", 6),
            ("Seeking quiet space to process, reflect, and restore internal balance", 8),
            ("Becoming intensely expressive and driving group momentum", 9)
        ]
    },
    {
        "id": "q9",
        "dimension": "Style",
        "text": "When presenting your work or ideas to others, how do you communicate?",
        "options": [
            ("Through compelling narratives, creative design, and aesthetics", 7),
            ("Through clear strategic frameworks and step-by-step logic", 3),
            ("Through authentic personal stories and relational connection", 4),
            ("Through rigorous evidence, research, and objective facts", 2)
        ]
    },
    {
        "id": "q10",
        "dimension": "Mission",
        "text": "What drives your sense of personal purpose in your career or ministry?",
        "options": [
            ("Fighting injustice and defending the rights of vulnerable people", 1),
            ("Pioneering breakthrough ideas that disrupt traditional markets", 5),
            ("Nurturing people to help them realize their true identity and gifts", 4),
            ("Mastering a specialized field of knowledge", 2)
        ]
    },
    {
        "id": "q11",
        "dimension": "Competency",
        "text": "Which skill set would you feel most confident teaching to others?",
        "options": [
            ("Strategic planning, goal setting, and project management", 3),
            ("Process engineering, quality control, and operational efficiency", 6),
            ("Creative writing, artistic composition, or visual design", 7),
            ("Holistic evaluation, environmental/systemic observation, and balance", 8)
        ]
    },
    {
        "id": "q12",
        "dimension": "Style",
        "text": "How do you prefer to handle interpersonal conflict?",
        "options": [
            ("Address it publicly and advocate firmly for a fair resolution", 1),
            ("Listen empathetically one-on-one and facilitate healing", 4),
            ("Analyze the root causes dispassionately and focus on facts", 2),
            ("Look for systemic balance and mediator solutions", 8)
        ]
    }
]

st.title('🧭 CoachMe Universal Diagnostic Tool')
st.caption('Discover Your Unique Wiring: Core Value Areas (CVAs), Person Code, Model Roles, Key Traits & Caution Areas')

st.sidebar.title('CoachMe Navigation')
nav = st.sidebar.radio('Go to:', ['1. Take Assessment', '2. View Diagnostic Results', '3. Framework Guide & Deployment'])

if 'user_answers' not in st.session_state:
    st.session_state.user_answers = {}
if 'completed' not in st.session_state:
    st.session_state.completed = False

if nav == '1. Take Assessment':
    st.subheader('📋 Personal Diagnostic Questionnaire')
    st.write('Answer the scenario questions below to evaluate your natural preferences across Mission (Why), Competency (What), and Style (How).')
    
    with st.form('assessment_form'):
        user_name = st.text_input('Full Name / Identifier:', value='Participant 1')
        
        scores = {i: 0 for i in range(1, 10)}
        
        for idx, q in enumerate(QUESTIONS):
            st.markdown(f"**Question {idx+1}: {q['text']}** *(Focus: {q['dimension']})*")
            choices = [opt[0] for opt in q['options']]
            selected = st.radio(f"Select your response for Q{idx+1}:", choices, key=f"q_{q['id']}", index=0)
            
            for opt_text, cva_id in q['options']:
                if opt_text == selected:
                    scores[cva_id] += 3
            st.markdown('---')
            
        submitted = st.form_submit_button('Generate Diagnostic Profile 🚀')
        
        if submitted:
            st.session_state.user_name = user_name
            st.session_state.scores = scores
            st.session_state.completed = True
            st.success("Assessment calculated successfully! Go to '2. View Diagnostic Results' in the sidebar to see your profile.")

elif nav == '2. View Diagnostic Results':
    if not st.session_state.completed:
        st.warning("Please complete the questionnaire in '1. Take Assessment' first!")
    else:
        scores = st.session_state.scores
        user_name = st.session_state.user_name
        
        sorted_cvas = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        high_triad = [item[0] for item in sorted_cvas[:3]]
        mid_triad = [item[0] for item in sorted_cvas[3:6]]
        low_triad = [item[0] for item in sorted_cvas[6:]]
        
        person_code = ' · '.join(map(str, high_triad))
        
        st.subheader(f'📊 Diagnostic Profile for {user_name}')
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric('Person Code (High Triad)', person_code, f"{CVA_INFO[high_triad[0]]['name']} + {CVA_INFO[high_triad[1]]['name']} + {CVA_INFO[high_triad[2]]['name']}")
            
        with col2:
            st.metric('Primary CVA Anchor', CVA_INFO[high_triad[0]]['name'], f"{CVA_INFO[high_triad[0]]['tagline']}")

        with col3:
            high_set = set(high_triad)
            matched_roles = {}
            for rule in MODEL_ROLE_RULES:
                if rule['trigger'](high_set):
                    matched_roles.update(rule['descriptions'])
            if not matched_roles:
                matched_roles = DEFAULT_MODEL_ROLES
                
            primary_role = list(matched_roles.keys())[0]
            st.metric('Primary Model Role', primary_role, list(matched_roles.values())[0])

        st.markdown('### 1. Core Value Area (CVA) Triad Distribution')
        
        chart_data = pd.DataFrame({
            'Career Value Area': [f"CVA {k}: {CVA_INFO[k]['name']}" for k in scores.keys()],
            'Diagnostic Energy Score': list(scores.values())
        })
        st.bar_chart(chart_data.set_index('Career Value Area'))
        
        tcol1, tcol2, tcol3 = st.columns(3)
        
        with tcol1:
            st.markdown('#### 🔥 High Triad (Person Code)')
            st.write('These top 3 areas form your core wiring and natural strengths.')
            for c_id in high_triad:
                st.info(f**CVA {c_id}: {CVA_INFO[c_id]['name']}** ({CVA_INFO[c_id]['tagline']})

{CVA_INFO[c_id]['description']}")

        with tcol2:
            st.markdown('#### ⚡ Mid Triad (Supporting Strengths)')
            st.write('Supporting areas where performance is steady and neutral.')
            for c_id in mid_triad:
                st.warning(f"**CVA {c_id}: {CVA_INFO[c_id]['name']}** ({CVA_INFO[c_id]['tagline']})

{CVA_INFO[c_id]['description']}")

        with tcol3:
            st.markdown('#### 🔋 Low Triad (Energy Drainers)')
            st.write('Areas requiring deliberate conscious effort and higher energy input.')
            for c_id in low_triad:
                st.error(f"**CVA {c_id}: {CVA_INFO[c_id]['name']}** ({CVA_INFO[c_id]['tagline']})

{CVA_INFO[c_id]['description']}")

        st.markdown('---')
        st.markdown('### 2. Model Roles (Vocational Sweet Spot)')
        st.write('Model Roles represent characteristic organizational functions you are inherently wired to play effectively.')
        
        r_cols = st.columns(len(matched_roles))
        for idx, (r_name, r_desc) in enumerate(matched_roles.items()):
            with r_cols[idx % len(r_cols)]:
                st.success(f"**{r_name}**

{r_desc}")

        st.markdown('---')
        st.markdown('### 3. Key Traits (Superpowers) vs. Caution Areas (Blindspots)')
        
        pcol1, pcol2 = st.columns(2)
        with pcol1:
            st.success('#### 🌟 Key Traits & Superpowers')
            st.write('Positive expressions of your High Triad wiring:')
            for c_id in high_triad:
                st.markdown(f"**CVA {c_id} ({CVA_INFO[c_id]['name']}):**")
                for kt in CVA_INFO[c_id]['key_traits']:
                    st.write(f"• {kt}")

        with pcol2:
            st.error('#### ⚠️ Caution Areas & Stress Friction')
            st.write('Potential blindspots when your top strengths are overused under stress:')
            for c_id in high_triad:
                st.markdown(f"**CVA {c_id} ({CVA_INFO[c_id]['name']}):**")
                for ca in CVA_INFO[c_id]['caution_areas']:
                    st.write(f"• {ca}")

        st.markdown('---')
        st.markdown('### 💾 Export Profile Results')
        export_data = {
            'participant': user_name,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'person_code': person_code,
            'high_triad': [CVA_INFO[i]['name'] for i in high_triad],
            'mid_triad': [CVA_INFO[i]['name'] for i in mid_triad],
            'low_triad': [CVA_INFO[i]['name'] for i in low_triad],
            'model_roles': list(matched_roles.keys()),
            'scores': scores
        }
        st.download_button(
            label='Download CoachMe Profile (JSON)',
            data=json.dumps(export_data, indent=4),
            file_name=f"CoachMe_Profile_{user_name.replace(' ', '_')}.json",
            mime='application/json'
        )

else:
    st.subheader('📖 CoachMe Framework & Deployment Guide')
    st.write('CoachMe is a deployment-ready assessment engine designed to help anyone discover how they are wired across all 9 Career Value Areas, Person Codes, Model Roles, Key Traits, and Caution Areas.')
