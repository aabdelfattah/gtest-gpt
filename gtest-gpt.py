import openai
import os
import clang.cindex
import argparse

model_id = 'gpt-3.5-turbo'
dir = 'test-units'
api_usage = 0

def chatgpt(conversation):
    global api_usage
    response = openai.ChatCompletion.create(
        model=model_id,
        messages=conversation
    )
    api_usage += response['usage']['total_tokens']
    # print('Total token consumed: {0}'.format(api_usage['total_tokens']))
    # stop means complete
    # print(response['choices'][0].finish_reason)
    # print(response['choices'][0].index)
    conversation.append({'role': response.choices[0].message.role, 'content': response.choices[0].message.content})
    return conversation

def init_testergpt():
    conversation = [
        {
            'role': 'system',
            'content': 'You are a helpful tester, and you are capable of using gtest framework to write unit tests for C code,\
                        I will write you a unit of C software split into functions,\
                        I would like that you for each of these functions write a unit test using gtest framework'
        }
    ]
    conversation = chatgpt(conversation)
    print ('TesterGPT Initialized\n'+
            'TesterGPT: {0}'.format(conversation[-1]['content'])
           )



def parse_c_file(file_path):

    # Initialize clang
    clang.cindex.Config.set_library_file('/usr/lib/llvm-14/lib/libclang.so.1')
    index = clang.cindex.Index.create()

    # Parse the C file
    translation_unit = index.parse(file_path)

    # Extract functions from the parsed C code
    function_dict = {}
    for node in translation_unit.cursor.walk_preorder():
        if node.kind == clang.cindex.CursorKind.FUNCTION_DECL:
            function_name = node.spelling
            tokens = list(node.get_tokens())
            tokens_spelling = [t.spelling for t in tokens]
            function_body = ''.join(tokens_spelling[tokens_spelling.index('{'):-1])
            function_dict[function_name] = function_body

    print('Functions found in {0}:'.format(file_path))
    print([f"{key}\n" for key, value in function_dict.items()])
    return function_dict

def extract_functions(filename):
    function_dict = parse_c_file(filename)
    function_list = [f"{key}\n{value}" for key, value in function_dict.items()]
    return function_list

def write_gtest(function_list):
    response =[]
    for function in function_list:
        conversation = [
                {
                'role': 'user',
                'content': 'Please write a unit test using gtest framework for the function {0}'.format(function)
                }
            ]
        conversation = chatgpt(conversation)
        response.append(conversation[-1]['content'])
    return response   


def arg_parse():
    parser = argparse.ArgumentParser(description='Generate Gtest unit tests using GPT-3')
    parser.add_argument('--openai-api-key', '-k' ,type=str, required=True,  help='OpenAI API key')

    args, remaining_args = parser.parse_known_args()

    return args


def main(args):
    openai.api_key = args.openai_api_key
    init_testergpt()
    with open('out_unit_tests2.c', 'w') as test_file:
        function_list = extract_functions('test-units/audit.c')
        response = write_gtest(function_list)
        test_file.write('\n'.join(response))

    
    print('Total token consumed: {0}'.format(api_usage))
    print('Price in USD: {0}'.format(api_usage/1000*0.002))


    
if __name__ == '__main__':
    args=arg_parse()
    main(args)
    