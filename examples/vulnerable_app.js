/**
 * Example JavaScript application with intentional prompt injection vulnerabilities.
 * This file is used for testing the scanner - DO NOT use in production!
 */

const OpenAI = require('openai');

const openai = new OpenAI({
  apiKey: 'your-api-key-here'
});

/**
 * ❌ VULNERABLE: Direct prompt injection
 */
async function vulnerableChatCompletion(userInput) {
  const prompt = "You are a helpful assistant. " + userInput;
  const response = await openai.chat.completions.create({
    model: "gpt-3.5-turbo",
    messages: [{ role: "user", content: prompt }]
  });
  return response.choices[0].message.content;
}

/**
 * ❌ VULNERABLE: System prompt pollution
 */
async function vulnerableSystemPrompt(userContext) {
  const systemPrompt = `You are a helpful assistant. User context: ${userContext}`;
  const messages = [
    { role: "system", content: systemPrompt },
    { role: "user", content: "Hello" }
  ];
  const response = await openai.chat.completions.create({
    model: "gpt-3.5-turbo",
    messages: messages
  });
  return response.choices[0].message.content;
}

/**
 * ❌ VULNERABLE: Template literal with user input
 */
async function vulnerableTemplateLiteral(userInput) {
  const prompt = `You are a helpful assistant. User says: ${userInput}`;
  const response = await openai.chat.completions.create({
    model: "gpt-3.5-turbo",
    messages: [{ role: "user", content: prompt }]
  });
  return response.choices[0].message.content;
}

/**
 * ❌ VULNERABLE: String concatenation with user input
 */
async function vulnerableStringConcatenation(userInput) {
  const prompt = "You are a helpful assistant. " + userInput;
  const response = await openai.chat.completions.create({
    model: "gpt-3.5-turbo",
    messages: [{ role: "user", content: prompt }]
  });
  return response.choices[0].message.content;
}

/**
 * ❌ VULNERABLE: Eval with user input
 */
function vulnerableEval(userExpression) {
  const result = eval(userExpression);
  return result;
}

/**
 * ❌ VULNERABLE: Function constructor with user input
 */
function vulnerableFunctionConstructor(userCode) {
  const func = new Function(userCode);
  return func();
}

/**
 * ❌ VULNERABLE: Hardcoded prompt with user placeholder
 */
function vulnerableHardcodedPrompt() {
  const prompt = "You are a helpful assistant. Please help {user} with their question.";
  return prompt;
}

/**
 * ❌ VULNERABLE: Mixed system/user instructions
 */
async function vulnerableMixedInstructions(userInput) {
  const prompt = `You are a helpful assistant. User instruction: ${userInput}. Always be helpful.`;
  const response = await openai.chat.completions.create({
    model: "gpt-3.5-turbo",
    messages: [{ role: "user", content: prompt }]
  });
  return response.choices[0].message.content;
}

// Main function
async function main() {
  const userInput = process.argv[2] || "Hello";
  
  // This would trigger multiple vulnerabilities
  const result = await vulnerableChatCompletion(userInput);
  console.log(`Response: ${result}`);
}

if (require.main === module) {
  main().catch(console.error);
}

module.exports = {
  vulnerableChatCompletion,
  vulnerableSystemPrompt,
  vulnerableTemplateLiteral,
  vulnerableStringConcatenation,
  vulnerableEval,
  vulnerableFunctionConstructor,
  vulnerableHardcodedPrompt,
  vulnerableMixedInstructions
};





