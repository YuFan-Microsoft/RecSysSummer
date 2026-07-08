# Copyright 2024 Bytedance Ltd. and/or its affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re
from collections import defaultdict
_SOLUTION_CLIP_CHARS = 50



def extract_sid_tokens(s: str) -> list[str]:
    # regex: \( <  任意非 > 字符  +  > \)
    pattern = r'<[^>]+>'
    tokens = re.findall(pattern, s)
    return tokens


def extract_solution(solution_str, method="strict"):
    assert method in ["strict", "flexible"]

    # Optimization: Regular expression matching on very long strings can be slow.
    # For math problems, the final answer is usually at the end.
    # We only match on the last 50 characters, which is a safe approximation for 50 tokens.
    if len(solution_str) > _SOLUTION_CLIP_CHARS:
        solution_str = solution_str[-_SOLUTION_CLIP_CHARS:]

    match = re.search(r"</think>\s*(.*)", solution_str, re.DOTALL)
    if match:
        final_answer = match.group(1).strip()
        answer_sids = extract_sid_tokens(final_answer)[:3]
        if len(answer_sids) == 3:
            return answer_sids
    return None
    

def calculate_reward(answer_sids, ground_truth_sids):
    current_score = 0.0
    if answer_sids[0] == ground_truth_sids[0]:
        current_score += 0.25
        if answer_sids[1] == ground_truth_sids[1]:
            current_score *= 2
            if answer_sids[2] == ground_truth_sids[2]:
                current_score *= 2
        
    return current_score



def calculate_format_reward(answer_sids, prefix_map):
    def is_valid_sid_sequence(sid_list):
        """
        Check if a SID sequence is valid according to prefix_map.
        No root/terminal nodes are used.
        """
        if len(sid_list) < 3:
            return False

        a, b, c = sid_list[:3]

        # Check prefix (a,) → next: b
        if (a,) not in prefix_map:
            return False
        if b not in prefix_map[(a,)]:
            return False

        # Check prefix (a, b) → next: c
        if (a, b) not in prefix_map:
            return False
        if c not in prefix_map[(a, b)]:
            return False

        return True

    format_scores = is_valid_sid_sequence(answer_sids)
    return format_scores




# def rule_base_reward(data_source, solution_str, ground_truth, extra_info=None):
#     answer = extract_solution(solution_str=solution_str)
#     ground_truth = extract_sid_tokens(ground_truth)[:3]

#     format_score = 0.1

#     if answer is None:
#         return 0
#     else:
#         return calculate_reward(answer, ground_truth) + format_score



def construct_prefix_allowed_hashmap(item_info_path):
    sid_pattern = re.compile(r"<[^>]+>")
    prefix_map = defaultdict(set)

    with open(item_info_path, "r") as f:
        lines = f.readlines()

    for line in lines:
        semantic_id = line.split("\t")[0].strip()
        sid_list = sid_pattern.findall(semantic_id)

        # sid_list should be length 3: [a, b, c]
        if len(sid_list) != 3:
            continue  # skip malformed rows

        a, b, c = sid_list
        # prefix: ("a",) → next: b
        prefix_map[(a,)].add(b)
        # prefix: ("a", "b") → next: c
        prefix_map[(a, b)].add(c)

    # Convert sets to lists for consistency
    prefix_map = {prefix: list(next_tokens) for prefix, next_tokens in prefix_map.items()}
    return prefix_map



class MyRewardComputer:
    def __init__(self):
        self.sid_hash = construct_prefix_allowed_hashmap(
            "./data/Amazon/info/Office_Products_5_2016-10-2018-11.txt"
        )

    def compute(
        self,
        data_source: str,
        solution_str: str,
        ground_truth: str,
        extra_info: dict | None = None,
    ) -> float:
        # breakpoint()
        answer = extract_solution(solution_str=solution_str)
        ground_truth = extract_sid_tokens(ground_truth)[:3]

        if answer is None:
            return 0
        else:
            return calculate_reward(answer, ground_truth) + 0.1 * calculate_format_reward(answer, self.sid_hash)



# ---- 模块级单例（懒加载） ----
_reward_computer: MyRewardComputer | None = None

def _get_reward_computer() -> MyRewardComputer:
    global _reward_computer
    if _reward_computer is None:
        # 只在第一次被调用时初始化一次
        _reward_computer = MyRewardComputer()
    return _reward_computer


# ---- 暴露给 VERL 的函数接口 ----
def rule_base_reward(data_source, solution_str, ground_truth, extra_info=None):
    rc = _get_reward_computer()
    return rc.compute(data_source, solution_str, ground_truth, extra_info)