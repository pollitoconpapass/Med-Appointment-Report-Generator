import spacy
from heapq import nlargest
from openai import AzureOpenAI
from string import punctuation
from spacy.lang.en.stop_words import STOP_WORDS


# === GPT-4 OPENAI ===
azure_endpoint = 'https://qhaligpt.openai.azure.com/'
api_key = '8635c6b24b154a17a23fee85ad474b78'
api_version = "2024-03-01-preview"
deployment_name = "qhali-embedding"

client = AzureOpenAI(
    api_key=api_key,
    api_version=api_version,
    azure_endpoint=azure_endpoint
)

def gpt4o_summarize(dialogue):
    response = client.chat.completions.create(
        model="gpt4-o",
        messages=[
            {"role": "system", "content": "Eres la secretaria de un doctor, toma la conversacion y resumela en un informe medico"},
            {"role": "user", "content": dialogue},
        ]
    )

    return response.choices[0].message.content


# === SPACY ===
def spacy_summarize(text):
    nlp = spacy.load('en_core_web_sm')
    doc= nlp(text)
    percentage = 0.2
    
    # The score of each word is kept in a frequency table
    freq_of_word=dict()
    
    # Text cleaning and vectorization 
    for word in doc:
        if word.text.lower() not in list(STOP_WORDS):
            if word.text.lower() not in punctuation:
                if word.text not in freq_of_word.keys():
                    freq_of_word[word.text] = 1
                else:
                    freq_of_word[word.text] += 1
                    
    # Maximum frequency of word
    max_freq=max(freq_of_word.values())
    
    # Normalization of word frequency
    for word in freq_of_word.keys():
        freq_of_word[word]=freq_of_word[word]/max_freq
        
    # In this part, each sentence is weighed based on how often it contains the token.
    sent_tokens= [sent for sent in doc.sents]
    sent_scores = dict()
    for sent in sent_tokens:
        for word in sent:
            if word.text.lower() in freq_of_word.keys():
                if sent not in sent_scores.keys():                            
                    sent_scores[sent]=freq_of_word[word.text.lower()]
                else:
                    sent_scores[sent]+=freq_of_word[word.text.lower()]
    
    
    len_tokens=int(len(sent_tokens)*percentage)
    
    # Make the summary:
    summary = nlargest(n = len_tokens, iterable = sent_scores,key=sent_scores.get)
    final_summary=[word.text for word in summary]
    summary=" ".join(final_summary)
    
    return summary


# === MAIN ===
dialogue = '''
Speaker A: Hola, buenos días. Buenos días, señor. Miguel García. Mucho gusto. Me llamo Nicolás. Soy un estudiante de medicina aquí en Loyola.

Speaker B: Mucho gusto, señor.

Speaker A: Un placer, señor. ¿Ahora dígame, qué lo trae la clínica hoy día, Miguel?

Speaker B: Señor, tengo un dolor del estómago.

Speaker A: Ay, lo siento. ¿Me puedes mostrar a dónde en el estómago te duele?

Speaker B: Es aquí en el centro. Me siento más aquí.

Speaker A: ¿Ok, entonces al centro del estómago hay radiación con el dolor?

Speaker B: Claro. El dolor se mueve a este lado. Empezó aquí y se mueve aquí.

Speaker A: Entonces el dolor empezó en el centro y se movió a la derecha. Claro, entiendo. Dígame más sobre la calidad del dolor. ¿Es intenso? ¿Es agudo?

Speaker B: Es intenso, pero más o menos me siento como una presión. Es una presión constante.

Speaker A: Entiendo, una presión constante. Dígame más sobre la intensidad del dolor en una escala al un al 10. ¿10 siendo el dolor más terrible, qué es el dolor?

Speaker B: Digo, un seis o siete.

Speaker A: Un seis o siete a peor.

Speaker B: Un siete. Es muy intenso. No puedo dormir.

Speaker A: Lo siento, Miguel. Miguel, dígame cuándo empezó el dolor.

Speaker B: El dolor empezó hace tres días.

Speaker A: Tres días atrás. ¿Y fue de repente o gradualmente?

Speaker B: De repente.

Speaker A: De repente. ¿Y ha sido agudo o crónico el dolor?

Speaker B: Crónico.

Speaker A: Crónico. ¿Miguel, me puedes decir más de la frecuencia del dolor? ¿Es intermitente, continuo o es progresivo?

Speaker B: Es continuo. Es usualmente por el día. Me siento el dolor constante.

Speaker A: Constantemente por el día. ¿Me podrías decir más sobre cuándo empieza el dolor? Si hay un escenario que empieza pues.

Speaker B: El dolor es más fuerte después de la comida. Si como comida picante o comida con mucha grasa, me molesta el estómago mucho.

Speaker A: Entiendo. ¿Entonces la comida picante te molesta?

Speaker B: El chile.

Speaker A: El chile. ¿Hay otras cosas que hacen el dolor peor?

Speaker B: No, no la comida. Y he estado tomando pastillas. Ayuda en la acidez.

Speaker A: ¿Pastilla para la acidez?

Speaker B: No recuerdo el nombre ahora, pero una.

Speaker A: Pastilla, pero para la acidez. Sí. Entiendo. ¿Entonces la comida lo hace peor y las pastillas para el ácido no te da alivio?

Speaker B: No mucho. Me ayuda un poco.

Speaker A: ¿Pero no hay algo que te da alivio?

Speaker B: No, estoy tratando de dormir por toda la noche. ¿Pero por qué el dolor? Despierto despierto en medianoche porque es tan intenso.

Speaker A: Lo siento, Miguel. Dígame, señor. ¿Hay otros síntomas que tienes?

Speaker B: No, no puedo comer mucho y por eso me siento débil y cansado.

Speaker A: Débil y cansado.

Speaker B: Pero el síntoma es el dolor.

Speaker A: Entiendo. ¿Y Miguel, te ha pasado esto antes?

Speaker B: Sí, algunas veces en el pasado. Pero no como eso. No como con el dolor intenso. Es diferente.

Speaker A: Es diferente. Esta vez es más intenso. Ok, entiendo. Entonces, Miguel, para ver si tengo toda la información correcta, me dices que tres días atrás te empezó a doler el estómago aquí el centro. Pero hay radiación a la derecha. Es bien intenso. ¿El dolor empezó de repente? Ha sido bien progresivo. Un dolor al seis, al siete se hace peor con la comida picante. Y después de comer no hay mucho alivio en tomar pastillas para la acidez. Otra cosa, te sientes débil y te sientes cansado porque te está afectando tu habilidad de dormir. ¿Suena bien?

Speaker B: Suena perfecto.

Speaker A: Muchas gracias Miguel. Gracias Miguel. Ahora me gustaría preguntarte más sobre tu historia médica.

Speaker B: Está bien.

Speaker A: ¿Tienes alguna enfermedad?

Speaker B: Claro, tengo diabetes e hipertensión.

Speaker A: Gracias. ¿Estás corriente con todos sus exámenes de salud y vacunas?

Speaker B: Pienso que sí. Tengo un médico regular y por eso mantengo todas las medicinas con él por todo el año.

Speaker A: Muy bien, muy bien. ¿Dígame, tienes una enfermedad psiquiátrica?

Speaker B: No.

Speaker A: ¿Has tenido algún accidente?

Speaker B: No.

Speaker A: ¿Has tenido alguna operación o cirugía?

Speaker B: No.

Speaker A: ¿Miguel, me puedes decir cuáles medicamentos tomas?

Speaker B: Si, tomo muchos, pero tomo metformina, lisinopril, aspirina y pienso que uno más, pero no recuerdo el nombre ahora, pero los tomo diario.

Speaker A: No te preocupes, ahí lo podemos ver en la computadora. ¿Me puedes decir si tienes alguna alergia, caro?

Speaker B: Tengo una alergia a las jaivas y las langostas.

Speaker A: Gracias. ¿Tomas alguna medicina alternativa?

Speaker B: ¿Alternativa? No.

Speaker A: Ahora me gustaría preguntarte sobre su vida, sus relaciones, su función sexual y sus hábitos. Son preguntas que le preguntamos a todos nuestros pacientes. ¿Está bien?

Speaker B: Sí.

Speaker A: Muy bien. ¿Dígame, con quién vives en casa?

Speaker B: Vivo en mi casa con mi esposa y mis tres niños.

Speaker A: Muy bien. ¿Y se sienten seguros en casa?

Speaker B: Sí.

Speaker A: Muy bien. ¿Cómo está tu relación con su esposa?

Speaker B: Es una buena relación. Algunos días es difícil porque porque tenemos tres niños, pero vale la pena. Sí, sí, es una buena relación.

Speaker A: Muy bien. ¿Tienes alguna preocupación con su función sexual?

Speaker B: No, no problema ahí.

Speaker A: Gracias. Cuéntame más sobre su dieta.

Speaker B: Sí, pues mi esposa cocina la mayoría de la comida para nuestra familia. Comimos comida mexicana, carne como pollo, verduras, camote. Tratamos a comer saludable por los niños.

Speaker A: Muy bien, gracias. ¿Cuántas horas al día duermes?

Speaker B: Es depende, pero usualmente duermo seis o.

Speaker A: 7 h. Seis a 7 h. Gracias. ¿Cuántas veces a la semana haces ejercicio?

Speaker B: Buena pregunta. Pero usualmente trato de andar con mi esposa después de la trabajo. Más o menos tres veces a la semana.

Speaker A: Tres veces. Gracias Miguel. ¿Dígame, fumas?

Speaker B: No, paré tres años en el pasado.

Speaker A: Tres años atrás. ¿Gracias Miguel, tomas alcohol?

Speaker B: Claro, tomo cerveza, 1 poco de tequila en los fines de semana.

Speaker A: ¿Y cuántos tragos a la semana dirías?

Speaker B: Es depende quien está en la casa conmigo. Si hay mis amigos, mi familia, vamos a tomar más. Pero usualmente dos o tres tragos a la semana.

Speaker A: Gracias. Gracias. ¿Y haces algunas drogas? No, ninguna droga. Gracias. Ahora me gustaría preguntarte sobre la historia médica de su familia. ¿Está bien?

Speaker B: Sí.

Speaker A: Gracias. Cuéntame sobre la salud de sus padres.

Speaker B: Mi mamá, ella está viva. Ella tiene hipertensión, pero buen salud. Y mi papá se falleció.

Speaker A: Lo siento. ¿Y cuántos años tenía su padre?

Speaker B: Cuando falleció, él tenía 63.

Speaker A: ¿63. Hay una historia de enfermedades significativas en su familia? Si.

Speaker B: Sí, en el lado de mi papá hay muchos primos con diabetes y hipertensión. Es muy común en la familia de mi mamá.

Speaker A: Entiendo. Gracias, Miguel. ¿Y tienes hermanos?

Speaker B: Claro, tengo seis hermanos.

Speaker A: ¿Y cómo está la salud de ellos?

Speaker B: Todos son saludables, todos tienen familias y son buenos.

Speaker A: Muy bien, gracias, Miguel. Ahora me gustaría preguntarte algunas preguntas, si puedes responder con sí o no. ¿En la última semana, has tenido cambio de apetito?

Speaker B: Sí, menos hambre.

Speaker A: Gracias. ¿En la última semana, has tenido algunas erupciones en su piel?

Speaker B: No.

Speaker A: ¿Cambio de vista?

Speaker B: No.

Speaker A: ¿Dolor de garganta?

Speaker B: No.

Speaker A: ¿Dificultad en respirar?

Speaker B: No.

Speaker A: ¿Dolor de pecho?

Speaker B: No.

Speaker A: ¿Dificultad en urinar?

Speaker B: No.

Speaker A: ¿Dolor de hueso o dolor de músculo?

Speaker B: No.

Speaker A: ¿Has sentido triste?

Speaker B: No.

Speaker A: ¿Con ansiedad?

Speaker B: Un poco ansiedad sobre mi estómago, pero sí.

Speaker A: Entiendo, gracias. ¿Has tenido alguna fiebre?

Speaker B: No.

Speaker A: ¿Has sangrado de algún lado? Ok, gracias Miguel. Ahora voy a hablar con el doctor y luego va a entrar. Le voy a contar sobre su dolor de estómago. Ya por tres días te ha dolido aquí al centro con radiación a la derecha y ha sido bien intenso. Te sientes débil y bastante cansado. ¿Hay alguna cosa que perdí o qué quieres agregar?

Speaker B: No, es todo. Muchas gracias, señor.

Speaker A: Sí, por supuesto. Un placer. Gracias, Miguel.
'''

summary = gpt4o_summarize(dialogue)
print(summary)
