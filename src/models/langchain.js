import { ChatOpenAI, OpenAIEmbeddings } from "@langchain/openai";
import { getKey, hasKey } from '../utils/keys.js';
import { appendFileSync } from 'fs';

export class LangChain {
    constructor(modelName, url) {
        let config = {};

        if (url)
            config.baseURL = url;

        if (hasKey('OPENAI_ORG_ID'))
            config.organization = getKey('OPENAI_ORG_ID');

        this.llm = new ChatOpenAI({
            model: modelName,
            apiKey: getKey('OPENAI_API_KEY'),
            organization: config.organization,
            baseURL: config.baseURL,
            stop: '***'
        });

    }


    async sendRequest(turns, systemMessage, stop_seq='***') {
        let messages = [{'role': 'system', 'content': systemMessage}].concat(turns);
        this.llm.stop = stop_seq;

        let res = null;
        try {
            console.log('Awaiting openai api response with langchain...')
            // console.log('Messages:', messages);
            let completion = await this.llm.invoke(messages);
            if (completion.response_metadata.finish_reason == 'length')
                throw new Error('Context length exceeded'); 
            console.log('Received.')
            res = completion.content;
        }
        catch (err) {
            if ((err.message == 'Context length exceeded' || err.code == 'context_length_exceeded') && turns.length > 1) {
                console.log('Context length exceeded, trying again with shorter context.');
                return await this.sendRequest(turns.slice(1), systemMessage, stop_seq);
            } else {
                console.log(err);
                res = 'My brain disconnected, try again.';
            }
        }

        let logText = "============================\n";
        logText += "Prompt:\n" + JSON.stringify(messages, null, 2).replace(/\\n/g, '\n'); + "\n\n";
        logText += "LLM Answer:\n" + res + "\n";
        logText += "============================\n\n";
      
        try {
          appendFileSync("LLM_logs.txt", logText, "utf8");
        } catch (err) {
          console.error("Failed to write LLL logs:", err);
        }


        return res;
    }

    async embed(text) {
        const embeddings = new OpenAIEmbeddings({
            apiKey: getKey('OPENAI_API_KEY'),
            encoding_format: 'float',
            model: "text-embedding-ada-002"
        });
        const ret = await embeddings.embedQuery(text);
        return ret
    }
}
