import ast
import importlib.util
import json
import math
from pathlib import Path
import tempfile
import unittest


MODULE_PATH = Path(__file__).with_name("evaluate_phase2_checkpoint.py")
SPEC = importlib.util.spec_from_file_location("evaluate_phase2_checkpoint", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load evaluation metrics from {MODULE_PATH}")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
calculate_metrics_from_rows = MODULE.calculate_metrics_from_rows
build_result_record = MODULE.build_result_record
write_results_jsonl = MODULE.write_results_jsonl

SLICE_MODULE_PATH = MODULE_PATH.parent.parent / "verl" / "trainer" / "ppo" / "sid_eval_slices.py"
SLICE_SPEC = importlib.util.spec_from_file_location("sid_eval_slices", SLICE_MODULE_PATH)
if SLICE_SPEC is None or SLICE_SPEC.loader is None:
    raise RuntimeError(f"Unable to load training evaluation slices from {SLICE_MODULE_PATH}")
SLICE_MODULE = importlib.util.module_from_spec(SLICE_SPEC)
SLICE_SPEC.loader.exec_module(SLICE_MODULE)

DATA_MODULE_PATH = MODULE_PATH.parent.parent / "data_Qwen3.py"
DATA_MODULE_TREE = ast.parse(DATA_MODULE_PATH.read_text(encoding="utf-8"))
RL_DATA_MODULE_PATH = MODULE_PATH.parent.parent / "phase3_rl" / "create_reasoning_rl_data.py"
RL_DATA_MODULE_TREE = ast.parse(RL_DATA_MODULE_PATH.read_text(encoding="utf-8"))


def _method(tree, class_name, method_name):
    class_node = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == class_name
    )
    return next(
        node
        for node in class_node.body
        if isinstance(node, ast.FunctionDef) and node.name == method_name
    )


def _evaluate_expression(expression, **values):
    compiled = compile(
        ast.fix_missing_locations(ast.Expression(expression)),
        filename=str(DATA_MODULE_PATH),
        mode="eval",
    )
    return eval(compiled, {}, values)


def _returned_dict_value(class_name, method_name, key, **values):
    for node in ast.walk(_method(DATA_MODULE_TREE, class_name, method_name)):
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Dict):
            for dict_key, expression in zip(node.value.keys, node.value.values):
                if isinstance(dict_key, ast.Constant) and dict_key.value == key:
                    return _evaluate_expression(expression, **values)
    raise LookupError((class_name, method_name, key))


def _assigned_value(class_name, method_name, variable_name, tree=DATA_MODULE_TREE):
    for node in ast.walk(_method(tree, class_name, method_name)):
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == variable_name
            for target in node.targets
        ):
            return _evaluate_expression(node.value)
    raise LookupError((class_name, method_name, variable_name))


def _returned_value(class_name, method_name, tree=DATA_MODULE_TREE, **values):
    return_node = next(
        node
        for node in ast.walk(_method(tree, class_name, method_name))
        if isinstance(node, ast.Return)
    )
    return _evaluate_expression(return_node.value, **values)


def _row(target, history_sids, target_rank=None):
    predictions = [f"<a_{index}><b_{index}><c_{index}>" for index in range(10)]
    if target_rank is not None:
        predictions[target_rank - 1] = target
    return {
        "output": target,
        "history_sids": history_sids,
        "predict": predictions,
    }


class GroupedEvaluationMetricsTest(unittest.TestCase):
    def test_reports_overall_novel_and_repeat_metrics(self):
        novel_target = "<a_20><b_20><c_20>"
        repeat_target = "<a_21><b_21><c_21>"
        missed_target = "<a_22><b_22><c_22>"
        rows = [
            _row(novel_target, ["<a_20><b_20><c_99>"], target_rank=6),
            _row(repeat_target, [repeat_target], target_rank=2),
            _row(missed_target, [], target_rank=None),
        ]
        known_sids = {
            prediction
            for row in rows
            for prediction in row["predict"]
        }

        metrics = calculate_metrics_from_rows(rows, known_sids)

        novel_gain = 1.0 / math.log2(7)
        repeat_gain = 1.0 / math.log2(3)
        self.assertEqual(metrics["rows"], 3)
        self.assertAlmostEqual(metrics["hr"]["5"], 1.0 / 3.0)
        self.assertAlmostEqual(metrics["hr"]["10"], 2.0 / 3.0)
        self.assertAlmostEqual(metrics["ndcg"]["10"], (novel_gain + repeat_gain) / 3.0)

        novel = metrics["groups"]["novel"]
        self.assertEqual(novel["rows"], 2)
        self.assertEqual(novel["hr"]["5"], 0.0)
        self.assertEqual(novel["hr"]["10"], 0.5)
        self.assertAlmostEqual(novel["ndcg"]["10"], novel_gain / 2.0)

        repeat = metrics["groups"]["repeat"]
        self.assertEqual(repeat["rows"], 1)
        self.assertEqual(repeat["hr"]["5"], 1.0)
        self.assertAlmostEqual(repeat["ndcg"]["5"], repeat_gain)

        training_metrics = SLICE_MODULE.compute_novel_repeat_ranking_metrics(
            [row["predict"] for row in rows],
            [row["output"] for row in rows],
            [row["history_sids"] for row in rows],
        )
        for group in ("novel", "repeat"):
            for metric_name in ("hr", "ndcg"):
                for cutoff in (5, 10):
                    training_value = SLICE_MODULE.mean_present_values(
                        training_metrics[f"sid_eval_{group}_{metric_name}_at_{cutoff}"]
                    )
                    self.assertAlmostEqual(
                        metrics["groups"][group][metric_name][str(cutoff)],
                        training_value,
                    )

    def test_empty_group_metrics_are_none(self):
        target = "<a_20><b_20><c_20>"
        row = _row(target, [], target_rank=1)

        metrics = calculate_metrics_from_rows([row], set(row["predict"]))

        self.assertEqual(metrics["groups"]["repeat"]["rows"], 0)
        self.assertIsNone(metrics["groups"]["repeat"]["hr"]["5"])
        self.assertIsNone(metrics["groups"]["repeat"]["ndcg"]["10"])

    def test_history_sids_are_required(self):
        row = _row("<a_20><b_20><c_20>", [], target_rank=1)
        del row["history_sids"]

        with self.assertRaisesRegex(ValueError, "row 0.*history_sids"):
            calculate_metrics_from_rows([row], set(row["predict"]))

    def test_writes_requested_jsonl_schema(self):
        sample = {
            "source_index": 12,
            "user_id": "A4449",
            "history_sids": ["<a_1><b_2><c_3>"],
            "history_title_list": ["History title"],
            "output": "<a_4><b_5><c_6>\n",
            "item_title": "Target title",
            "cot": "<think>\nreasoning",
            "predict": [f"<a_{index}><b_{index}><c_{index}>" for index in range(12)],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "results.jsonl"
            count = write_results_jsonl(output_path, [sample])
            lines = output_path.read_text(encoding="utf-8").splitlines()

        self.assertEqual(count, 1)
        self.assertEqual(len(lines), 1)
        self.assertEqual(
            json.loads(lines[0]),
            {
                "source_index": 12,
                "user_id": "A4449",
                "history_sid_list": ["<a_1><b_2><c_3>"],
                "history_title_list": ["History title"],
                "item_sid": "<a_4><b_5><c_6>",
                "item_title": "Target title",
                "generated_reasoning_path": "<think>\nreasoning",
                "prediction_beam_10": [
                    f"<a_{index}><b_{index}><c_{index}>"
                    for index in range(10)
                ],
            },
        )

    def test_rejects_misaligned_history_titles(self):
        sample = {
            "history_sids": ["<a_1><b_2><c_3>"],
            "history_title_list": [],
        }

        with self.assertRaisesRegex(ValueError, "mismatched history SID/title lengths"):
            build_result_record(sample, fallback_source_index=0)


class EvaluationPromptContractTest(unittest.TestCase):
    def test_no_thinking_prompt_remains_byte_for_byte_original(self):
        self.assertEqual(
            _returned_dict_value(
                "SidNextItemEvalDataset",
                "get_history",
                "input",
                history="<a_1><b_2><c_3>",
            ),
            "Can you predict the next possible item the user may expect, given the "
            "following chronological interaction history: <a_1><b_2><c_3>",
        )
        self.assertEqual(
            _assigned_value("SidNextItemEvalDataset", "pre", "instruction"),
            "Below is an instruction that describes a task, paired with an input that "
            "provides further context. Write a response that appropriately completes the request. \n"
            "Can you predict the next possible item that the user may expect?\n",
        )
        self.assertEqual(
            _assigned_value("SidNextItemEvalDataset", "pre", "prefix_prompt"),
            "<think>\n</think>\n\n",
        )

    def test_thinking_evaluation_prompt_matches_phase2_training(self):
        history = "<a_1><b_2><c_3>"
        thinking_user = _returned_value(
            "ReasoningEvalDataset",
            "generate_prompt_title",
            history=history,
        )
        training_user = _returned_value(
            "ReasoningActivationDataset",
            "generate_prompt_title",
            history=history,
        )
        self.assertEqual(thinking_user, training_user)
        self.assertEqual(
            _assigned_value("ReasoningEvalDataset", "pre", "instruction"),
            _assigned_value("ReasoningActivationDataset", "pre", "instruction"),
        )

    def test_phase3_rl_prompt_matches_phase2_training(self):
        history = "<a_1><b_2><c_3>"
        self.assertEqual(
            _returned_value(
                "Reasoning_RL_Dataset",
                "generate_prompt_title",
                tree=RL_DATA_MODULE_TREE,
                history=history,
            ),
            _returned_value(
                "ReasoningActivationDataset",
                "generate_prompt_title",
                history=history,
            ),
        )
        self.assertEqual(
            _assigned_value(
                "Reasoning_RL_Dataset",
                "pre",
                "instruction",
                tree=RL_DATA_MODULE_TREE,
            ),
            _assigned_value("ReasoningActivationDataset", "pre", "instruction"),
        )


if __name__ == "__main__":
    unittest.main()